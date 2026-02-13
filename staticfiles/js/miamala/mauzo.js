class MauzoManager {
  constructor() {
    this.config = {
      columnIndices: [0, 1, 2, 3, 4, 5],
      dateCache: { start: null, end: null },
      csrfToken: this.getCSRFToken(),
      deletingState: false,
    };

    this.selectors = {
      newMauzoForm: "#new_mauzo_form",
      editMauzoForm: "#edit_mauzo_form",
      deleteMauzoForm: "#del_mauzo_form",
      table: "#mauzo_table",
      newMauzoBtn: "#new_mauzo_btn",
      editMauzoBtn: "#mauzo_edit_btn",
      deleteMauzoBtn: "#mauzo_delete_btn",
      searchInput: "#search_mauzo_field",
      clearFilter: "#mauzo_filter_clear",
      minDate: "#min_mauzo_date",
      maxDate: "#max_mauzo_date",
      dateClear: "#date_filter_clear",
      dateFilterBtn: "#date_filter_btn",
      mauzoListUrl: "#mauzo_list_url",
      mauzoId: "#mauzo_id",
      mauzoDelId: "#mauzo_del_id",
      viewMauzoModal: "#view_mauzo_modal",
      updateMauzoModal: "#update_mauzo_modal",
      deleteMauzoModal: "#delete_mauzo_modal",
      dateFilterModal: "#dateFilterModal",
      mauzo_shops: "#mauzo_shop",
      mauzo_users: "#mauzo_users",
    };

    this.table = null;
    this.shopOptions = null;
    this.userOptions = null;
    this.init();
  }

  /**
   * Get CSRF token from meta tag
   */
  getCSRFToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    return metaTag ? metaTag.getAttribute("content") : "";
  }

  /**
   * Initialize the application
   */
  init() {
    this.shopOptions = $(`${this.selectors.mauzo_shops} option`);
    this.userOptions = $(`${this.selectors.mauzo_users} option`);
    this.setupFormHandlers();
    this.setupTable();
    this.setupEventHandlers();
  }

  /**
   * Generate alert messages
   */
  generateAlert(isSuccess, message, icon = null) {
    const iconClass =
      icon || (isSuccess ? "check-circle" : "exclamation-circle");
    return `<i class="fas fa-${iconClass}"></i> &nbsp; ${message}`;
  }

  /**
   * Format dates for display
   */
  formatDates(dateStr, format = "date") {
    const date = dateStr === "today" ? new Date() : new Date(dateStr);
    const months = [
      "Jan",
      "Feb",
      "Mar",
      "Apr",
      "May",
      "Jun",
      "Jul",
      "Aug",
      "Sept",
      "Oct",
      "Nov",
      "Dec",
    ];

    const day = date.getDate().toString().padStart(2, "0");
    const hours = date.getHours().toString().padStart(2, "0");
    const minutes = date.getMinutes().toString().padStart(2, "0");

    if (format === "datetime") {
      return `${day}-${
        months[date.getMonth()]
      }-${date.getFullYear()} ${hours}:${minutes}`;
    }
    return `${day}-${months[date.getMonth()]}-${date.getFullYear()}`;
  }

  /**
   * Get date range for filtering
   */
  getDateRange() {
    const minDateStr = $(this.selectors.minDate).val();
    const maxDateStr = $(this.selectors.maxDate).val();

    this.config.dateCache.start = minDateStr || null;
    this.config.dateCache.end = maxDateStr || null;

    return {
      start: this.config.dateCache.start,
      end: this.config.dateCache.end,
    };
  }

  /**
   * Clear date filters
   */
  clearDates() {
    $(this.selectors.minDate).val("");
    $(this.selectors.maxDate).val("");
    this.config.dateCache.start = null;
    this.config.dateCache.end = null;
  }

  /**
   * Setup all form handlers
   */
  setupFormHandlers() {
    this.setupNewMauzoHandler();
    this.setupEditMauzoHandler();
    this.setupDeleteMauzoHandler();
  }

  /**
   * Setup new mauzo form handler
   */
  setupNewMauzoHandler() {
    $(this.selectors.newMauzoForm).on("submit", (e) =>
      this.handleNewMauzoSubmit(e),
    );
  }

  /**
   * Handle new mauzo form submission
   */
  handleNewMauzoSubmit(e) {
    e.preventDefault();
    const form = $(this.selectors.newMauzoForm);
    const formSms = form.find(".formsms");
    const submitBtn = $(this.selectors.newMauzoBtn);

    $.ajax({
      type: "POST",
      url: form.attr("action"),
      data: new FormData(form[0]),
      dataType: "json",
      contentType: false,
      processData: false,
      headers: { "X-CSRFToken": this.config.csrfToken },
      beforeSend: () => this.setButtonLoading(submitBtn, "spinner"),
      success: (response) =>
        this.handleNewMauzoSuccess(response, formSms, submitBtn),
      error: (xhr, status, error) => {
        console.error(error);
        this.resetButton(submitBtn, "Record");
      },
    });
  }

  /**
   * Handle new mauzo success response
   */
  handleNewMauzoSuccess(response, formSms, submitBtn) {
    this.resetButton(submitBtn, "Record");

    const alert = this.generateAlert(response.success, response.sms);
    const alertClass = response.success ? "alert-success" : "alert-danger";

    formSms
      .removeClass("alert-success alert-danger")
      .addClass(alertClass)
      .html(alert)
      .slideDown("fast")
      .delay(2000)
      .slideUp("fast");

    if (response.success) {
      $(this.selectors.newMauzoForm)[0].reset();
      this.table.draw();
    }
  }

  /**
   * Setup edit mauzo form handler
   */
  setupEditMauzoHandler() {
    $(this.selectors.editMauzoForm).on("submit", (e) =>
      this.handleEditMauzoSubmit(e),
    );
  }

  /**
   * Handle edit mauzo form submission
   */
  handleEditMauzoSubmit(e) {
    e.preventDefault();
    const form = $(this.selectors.editMauzoForm);
    const formSms = form.find(".formsms");
    const submitBtn = $(this.selectors.editMauzoBtn);

    $.ajax({
      type: "POST",
      url: form.attr("action"),
      data: new FormData(form[0]),
      dataType: "json",
      contentType: false,
      processData: false,
      headers: { "X-CSRFToken": this.config.csrfToken },
      beforeSend: () => this.setButtonLoading(submitBtn, "spinner"),
      success: (response) =>
        this.handleEditMauzoSuccess(response, formSms, submitBtn),
      error: (xhr, status, error) => {
        console.error(error);
        this.resetButton(submitBtn, "Update");
      },
    });
  }

  /**
   * Handle edit mauzo success response
   */
  handleEditMauzoSuccess(response, formSms, submitBtn) {
    this.resetButton(submitBtn, "Update");

    const alert = this.generateAlert(response.success, response.sms);
    const alertClass = response.success ? "alert-success" : "alert-danger";

    formSms
      .removeClass("alert-success alert-danger")
      .addClass(alertClass)
      .html(alert)
      .slideDown("fast")
      .delay(2000)
      .slideUp("fast");

    if (response.success) {
      this.table.draw();
    }
  }

  /**
   * Setup delete mauzo form handler
   */
  setupDeleteMauzoHandler() {
    $(this.selectors.deleteMauzoForm).on("submit", (e) =>
      this.handleDeleteMauzoSubmit(e),
    );
  }

  /**
   * Handle delete mauzo form submission
   */
  handleDeleteMauzoSubmit(e) {
    e.preventDefault();
    const form = $(this.selectors.deleteMauzoForm);
    const formSms = form.find(".formsms");
    const submitBtn = $(this.selectors.deleteMauzoBtn);

    $.ajax({
      type: "POST",
      url: form.attr("action"),
      data: new FormData(form[0]),
      dataType: "json",
      contentType: false,
      processData: false,
      headers: { "X-CSRFToken": this.config.csrfToken },
      beforeSend: () => this.setButtonLoading(submitBtn, "spinner"),
      success: (response) =>
        this.handleDeleteMauzoSuccess(response, formSms, submitBtn),
      error: (xhr, status, error) => {
        console.error(error);
        this.resetButton(submitBtn, "Yes");
      },
    });
  }

  /**
   * Handle delete mauzo success response
   */
  handleDeleteMauzoSuccess(response, formSms, submitBtn) {
    this.resetButton(submitBtn, "Yes");

    if (response.success) {
      $(this.selectors.mauzoDelId).val("");
      $(this.selectors.deleteMauzoModal).modal("hide");
      this.table.draw();
    } else {
      const alert = this.generateAlert(response.success, response.sms);
      formSms
        .removeClass("alert-success")
        .addClass("alert-danger")
        .html(alert)
        .slideDown("fast")
        .delay(2000)
        .slideUp("fast");
    }
  }

  /**
   * Set button loading state
   */
  setButtonLoading(button, type) {
    if (type === "spinner") {
      button
        .html("<i class='fas fa-spinner fa-pulse'></i>")
        .attr("type", "button");
    }
  }

  /**
   * Reset button to normal state
   */
  resetButton(button, text) {
    button.html(text).attr("type", "submit");
  }

  /**
   * Fetch mauzo details for view/edit
   */
  fetchMauzoDetails(mauzoId, action) {
    const formData = new FormData();
    formData.append("mauzo_view", mauzoId);

    $.ajax({
      type: "POST",
      url: $(this.selectors.newMauzoForm).attr("action"),
      data: formData,
      dataType: "json",
      contentType: false,
      processData: false,
      headers: { "X-CSRFToken": this.config.csrfToken },
      success: (response) => this.handleFetchSuccess(response, action, mauzoId),
      error: (xhr, status, error) => {
        console.log(error);
        this.handleFetchError(action);
      },
    });
  }

  /**
   * Handle fetch success response
   */
  handleFetchSuccess(response, action, mauzoId) {
    if (response.success) {
      if (action === "view") {
        this.populateViewModal(response);
      } else if (action === "edit") {
        this.populateEditModal(response, mauzoId);
      }
    } else {
      this.handleFetchError(action);
    }
  }

  /**
   * Handle fetch error
   */
  handleFetchError(action) {
    const errorMessage =
      action === "view"
        ? "Failed to load sale/mauzo details."
        : "Failed to load current sale/mauzo details.";

    const modalSelector =
      action === "view"
        ? this.selectors.viewMauzoModal
        : this.selectors.updateMauzoModal;

    $(`${modalSelector} .modal-footer`).show("fast");
    $(`${modalSelector} .loading`).html(
      `<i class="fas fa-exclamation-circle"></i> &nbsp; ${errorMessage}`,
    );
  }

  /**
   * Populate view modal with mauzo details
   */
  populateViewModal(response) {
    $("#date_record").text(response.regdate);
    $("#date_updated").text(response.updatedate);
    $("#date_mauzo").text(response.dates);
    $("#amount_mauzo").text(response.amount);
    $("#describe_mauzo").html(response.describe);
    $("#user_mauzo").text(response.user);
    $("#shop_mauzo").html(response.shop);

    $(`${this.selectors.viewMauzoModal} .loading`).hide("fast");
    $(`${this.selectors.viewMauzoModal} .details`).slideDown("fast");
    $(`${this.selectors.viewMauzoModal} .modal-footer`).slideDown("fast");
  }

  /**
   * Populate edit modal with mauzo details
   */
  populateEditModal(response, mauzoId) {
    const describe = response.describe === "N/A" ? "" : response.describe;

    $("#edit_mauzo_date").val(response.dates_form);
    $("#edit_mauzo_shop").val(response.shop_id).change();
    $("#edit_mauzo_amount").val(response.amount_form);
    $("#edit_mauzo_description").val(describe);
    $(this.selectors.mauzoId).val(mauzoId);

    $(`${this.selectors.updateMauzoModal} .loading`).hide("fast");
    $(`${this.selectors.updateMauzoModal} .mauzo_form`).slideDown("fast");
    $(`${this.selectors.updateMauzoModal} .modal-footer`).slideDown("fast");
  }

  /**
   * Fill edit form - handles view, edit, and delete actions
   */
  fillEditForm(id, action) {
    if (action === "edit") {
      $(`${this.selectors.updateMauzoModal} .mauzo_form`).hide("fast");
      $(`${this.selectors.updateMauzoModal} .modal-footer`).hide("fast");
      $(`${this.selectors.updateMauzoModal} .loading`).show("fast");
      $(this.selectors.updateMauzoModal).modal("show");
      this.fetchMauzoDetails(id, "edit");
    } else if (action === "view") {
      $(`${this.selectors.viewMauzoModal} .details`).hide("fast");
      $(`${this.selectors.viewMauzoModal} .modal-footer`).hide("fast");
      $(`${this.selectors.viewMauzoModal} .loading`).show("fast");
      $(this.selectors.viewMauzoModal).modal("show");
      this.fetchMauzoDetails(id, "view");
    } else if (action === "del") {
      $(this.selectors.mauzoDelId).val(parseInt(id));
      $(this.selectors.deleteMauzoModal).modal("show");
    }
  }

  /**
   * Setup DataTable
   */
  setupTable() {
    // Clone header for filters
    $(`${this.selectors.table} thead tr`)
      .clone(true)
      .attr("class", "filters")
      .appendTo(`${this.selectors.table} thead`);

    this.table = $(this.selectors.table).DataTable({
      fixedHeader: true,
      processing: true,
      serverSide: true,
      ajax: this.getAjaxConfig(),
      columns: this.getColumnConfig(),
      order: [[1, "desc"]],
      paging: true,
      pageLength: 10,
      lengthChange: true,
      autoWidth: true,
      searching: true,
      bInfo: true,
      bSort: true,
      orderCellsTop: true,
      columnDefs: this.getColumnDefs(),
      dom: "lBfrtip",
      drawCallback: (response) => this.handleDrawCallback(response),
      initComplete: () => this.initTableFilters(),
    });
  }

  /**
   * Get AJAX configuration for DataTable
   */
  getAjaxConfig() {
    return {
      url: $(this.selectors.mauzoListUrl).val(),
      type: "POST",
      data: (d) => {
        const dateRange = this.getDateRange();
        d.startdate = dateRange.start;
        d.enddate = dateRange.end;
      },
      dataType: "json",
      headers: { "X-CSRFToken": this.config.csrfToken },
    };
  }

  /**
   * Get column configuration
   */
  getColumnConfig() {
    return [
      { data: "count" },
      { data: "dates" },
      { data: "amount" },
      { data: "user" },
      { data: "shop" },
      { data: "action" },
    ];
  }

  /**
   * Get column definitions
   */
  getColumnDefs() {
    return [
      {
        targets: [0, 5],
        orderable: false,
      },
      {
        targets: 5,
        createdCell: (cell, cellData, rowData) => {
          const buttons = `
            <button class="btn btn-sm btn-dblue text-white me-1" onclick="mauzoManager.fillEditForm(${rowData.id}, 'edit')">
              <i class="fas fa-edit"></i>
            </button>
            <button class="btn btn-sm btn-danger me-1" onclick="mauzoManager.fillEditForm(${rowData.id}, 'del')">
              <i class="fas fa-trash"></i>
            </button>
            <button class="btn btn-sm btn-success" onclick="mauzoManager.fillEditForm(${rowData.id}, 'view')">
              <i class="fas fa-eye"></i>
            </button>
          `;
          $(cell).html(buttons);
        },
      },
      {
        targets: "_all",
        className: "align-middle text-nowrap text-center",
      },
      {
        targets: [1, 3, 4],
        createdCell: (cell) => {
          $(cell).removeClass("text-center").addClass("text-start ps-3");
        },
      },
      {
        targets: 2,
        createdCell: (cell) => {
          $(cell).removeClass("text-center").addClass("text-end pe-4");
        },
      },
    ];
  }

  /**
   * Handle DataTable draw callback
   */
  handleDrawCallback(response) {
    this.updateFooter({ total_amount: response.json.total_amount });
  }

  /**
   * Initialize table filters
   */
  initTableFilters() {
    const api = this.table;

    api
      .columns(this.config.columnIndices)
      .eq(0)
      .each((colIdx) => {
        const cell = $(".filters th").eq(
          $(api.column(colIdx).header()).index(),
        );
        cell.addClass("bg-white");

        if (colIdx === 0 || colIdx === 5) {
          cell.html("");
        } else if (colIdx === 1) {
          const calendar = `
            <button type="button" class="btn btn-primary text-white" 
                    data-bs-toggle="modal" data-bs-target="${this.selectors.dateFilterModal}">
              <i class="fas fa-calendar-alt"></i>
            </button>
          `;
          cell.html(calendar).addClass("text-center");
        } else if (colIdx === 3) {
          this.setupUserFilter(cell, api, colIdx);
        } else if (colIdx === 4) {
          this.setupShopFilter(cell, api, colIdx);
        } else {
          cell
            .html(
              "<input type='text' class='form-control d-inline-block w-auto' placeholder='Filter'/>",
            )
            .addClass("text-center");
          this.setupColumnFilter(cell, api, colIdx);
        }
      });
  }

  /**
   * Setup user filter dropdown
   */
  setupUserFilter(cell, api, colIdx) {
    const select = document.createElement("select");
    select.className = "select-filter text-charcoal float-start";
    select.innerHTML = `<option value="">All</option>`;

    this.userOptions.each((index, option) => {
      const optionText = $(option).text();
      select.innerHTML += `<option value="${optionText}">${optionText}</option>`;
    });

    cell.html(select);
    $(select).on("change", function () {
      api.column(colIdx).search($(this).val()).draw();
    });
  }

  /**
   * Setup shop filter dropdown
   */
  setupShopFilter(cell, api, colIdx) {
    const select = document.createElement("select");
    select.className = "select-filter text-charcoal float-start";
    select.innerHTML = `<option value="">All</option>`;

    this.shopOptions.each((index, option) => {
      if (index === 0) return;
      const optionText = $(option).text();
      select.innerHTML += `<option value="${optionText}">${optionText}</option>`;
    });

    cell.html(select);
    $(select).on("change", function () {
      api.column(colIdx).search($(this).val()).draw();
    });
  }

  /**
   * Setup individual column filter
   */
  setupColumnFilter(cell, api, colIdx) {
    const input = $("input", cell);

    input.off("keyup change").on("keyup change", function (e) {
      e.stopPropagation();
      $(this).attr("title", $(this).val());

      const regexr = "{search}";
      const cursorPosition = this.selectionStart;

      api
        .column(colIdx)
        .search(
          this.value !== "" ? regexr.replace("{search}", this.value) : "",
          this.value !== "",
          this.value === "",
        )
        .draw();

      $(this).focus()[0].setSelectionRange(cursorPosition, cursorPosition);
    });
  }

  /**
   * Update footer values
   */
  updateFooter(totals) {
    const footer = $(this.table.table().footer());
    let reportDates = "All time";

    const dateStart = $(this.selectors.minDate).val();
    const dateEnd = $(this.selectors.maxDate).val();

    if (dateStart && dateEnd) {
      reportDates = `${this.formatDates(dateStart)} - ${this.formatDates(
        dateEnd,
      )}`;
    } else if (dateStart) {
      reportDates = `From ${this.formatDates(dateStart)}`;
    } else if (dateEnd) {
      reportDates = `Up to ${this.formatDates(dateEnd)}`;
    }

    const tr = footer.find("tr:eq(0)");
    tr.find("th:eq(1)").text(reportDates);
    tr.find("th:eq(2)").text(totals.total_amount);
  }

  /**
   * Setup all event handlers
   */
  setupEventHandlers() {
    this.setupSearchHandler();
    this.setupFilterHandlers();
  }

  /**
   * Setup search handler
   */
  setupSearchHandler() {
    $(this.selectors.searchInput)
      .off("keyup")
      .on("keyup", () => {
        this.table.search($(this.selectors.searchInput).val()).draw();
      });
  }

  /**
   * Setup filter handlers
   */
  setupFilterHandlers() {
    $(this.selectors.clearFilter)
      .off("click")
      .on("click", (e) => {
        e.preventDefault();
        $(this.selectors.searchInput).val("");
        this.clearDates();
        $('.filters input[type="text"]').val("");
        $(".filters select").val("");
        this.table.search("").columns().search("").draw();
      });

    $(this.selectors.dateClear)
      .off("click")
      .on("click", () => this.clearDates());

    $(this.selectors.dateFilterBtn)
      .off("click")
      .on("click", () => this.table.draw());
  }
}

// Initialize the application when DOM is ready and expose globally for onclick handlers
let mauzoManager;
$(function () {
  mauzoManager = new MauzoManager();
});

// Legacy function support for existing onclick handlers
function fill_edit_form(id, str) {
  if (window.mauzoManager) {
    window.mauzoManager.fillEditForm(id, str);
  }
}
