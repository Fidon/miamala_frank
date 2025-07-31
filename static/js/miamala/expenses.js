class ExpensesManager {
  constructor() {
    this.config = {
      columnIndices: [0, 1, 2, 3, 4, 5, 6],
      dateCache: { start: null, end: null },
      csrfToken: this.getCSRFToken(),
      deletingState: false,
    };

    this.selectors = {
      newExpForm: "#new_exp_form",
      editExpForm: "#edit_exp_form",
      deleteExpForm: "#del_exp_form",
      table: "#expenses_table",
      newExpBtn: "#new_exp_btn",
      editExpBtn: "#exp_edit_btn",
      deleteExpBtn: "#exp_delete_btn",
      searchInput: "#search_exp_field",
      clearFilter: "#expense_filter_clear",
      minDate: "#min_exp_date",
      maxDate: "#max_exp_date",
      dateClear: "#date_filter_clear",
      dateFilterBtn: "#date_filter_btn",
      expensesListUrl: "#expenses_list_url",
      expenseId: "#expense_id",
      expenseDelId: "#expense_del_id",
      viewExpModal: "#view_exp_modal",
      updateExpModal: "#update_exp_modal",
      deleteExpModal: "#delete_exp_modal",
      dateFilterModal: "#dateFilterModal",
    };

    this.table = null;
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
    this.setupNewExpenseHandler();
    this.setupEditExpenseHandler();
    this.setupDeleteExpenseHandler();
  }

  /**
   * Setup new expense form handler
   */
  setupNewExpenseHandler() {
    $(this.selectors.newExpForm).on("submit", (e) =>
      this.handleNewExpenseSubmit(e)
    );
  }

  /**
   * Handle new expense form submission
   */
  handleNewExpenseSubmit(e) {
    e.preventDefault();
    const form = $(this.selectors.newExpForm);
    const formSms = form.find(".formsms");
    const submitBtn = $(this.selectors.newExpBtn);

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
        this.handleNewExpenseSuccess(response, formSms, submitBtn),
      error: (xhr, status, error) => {
        console.error(error);
        this.resetButton(submitBtn, "Add");
      },
    });
  }

  /**
   * Handle new expense success response
   */
  handleNewExpenseSuccess(response, formSms, submitBtn) {
    this.resetButton(submitBtn, "Add");

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
      $(this.selectors.newExpForm)[0].reset();
      this.table.draw();
    }
  }

  /**
   * Setup edit expense form handler
   */
  setupEditExpenseHandler() {
    $(this.selectors.editExpForm).on("submit", (e) =>
      this.handleEditExpenseSubmit(e)
    );
  }

  /**
   * Handle edit expense form submission
   */
  handleEditExpenseSubmit(e) {
    e.preventDefault();
    const form = $(this.selectors.editExpForm);
    const formSms = form.find(".formsms");
    const submitBtn = $(this.selectors.editExpBtn);

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
        this.handleEditExpenseSuccess(response, formSms, submitBtn),
      error: (xhr, status, error) => {
        console.error(error);
        this.resetButton(submitBtn, "Update");
      },
    });
  }

  /**
   * Handle edit expense success response
   */
  handleEditExpenseSuccess(response, formSms, submitBtn) {
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
   * Setup delete expense form handler
   */
  setupDeleteExpenseHandler() {
    $(this.selectors.deleteExpForm).on("submit", (e) =>
      this.handleDeleteExpenseSubmit(e)
    );
  }

  /**
   * Handle delete expense form submission
   */
  handleDeleteExpenseSubmit(e) {
    e.preventDefault();
    const form = $(this.selectors.deleteExpForm);
    const formSms = form.find(".formsms");
    const submitBtn = $(this.selectors.deleteExpBtn);

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
        this.handleDeleteExpenseSuccess(response, formSms, submitBtn),
      error: (xhr, status, error) => {
        console.error(error);
        this.resetButton(submitBtn, "Yes");
      },
    });
  }

  /**
   * Handle delete expense success response
   */
  handleDeleteExpenseSuccess(response, formSms, submitBtn) {
    this.resetButton(submitBtn, "Yes");

    if (response.success) {
      $(this.selectors.expenseDelId).val("");
      $(this.selectors.deleteExpModal).modal("hide");
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
   * Fetch expense details for view/edit
   */
  fetchExpenseDetails(expenseId, action) {
    const formData = new FormData();
    formData.append("expense_view", expenseId);

    $.ajax({
      type: "POST",
      url: $(this.selectors.newExpForm).attr("action"),
      data: formData,
      dataType: "json",
      contentType: false,
      processData: false,
      headers: { "X-CSRFToken": this.config.csrfToken },
      success: (response) =>
        this.handleFetchSuccess(response, action, expenseId),
      error: (xhr, status, error) => {
        console.log(error);
        this.handleFetchError(action);
      },
    });
  }

  /**
   * Handle fetch success response
   */
  handleFetchSuccess(response, action, expenseId) {
    if (response.success) {
      if (action === "view") {
        this.populateViewModal(response);
      } else if (action === "edit") {
        this.populateEditModal(response, expenseId);
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
        ? "Failed to load expense details."
        : "Failed to load current expense details.";

    const modalSelector =
      action === "view"
        ? this.selectors.viewExpModal
        : this.selectors.updateExpModal;

    $(`${modalSelector} .modal-footer`).show("fast");
    $(`${modalSelector} .loading`).html(
      `<i class="fas fa-exclamation-circle"></i> &nbsp; ${errorMessage}`
    );
  }

  /**
   * Populate view modal with expense details
   */
  populateViewModal(response) {
    $("#date_record").text(response.regdate);
    $("#date_expense").text(response.dates);
    $("#title_expense").text(response.title);
    $("#amount_expense").text(response.amount);
    $("#describe_expense").html(response.describe);
    $("#user_expense").text(response.user);
    $("#shop_expense").html(response.shop);

    $(`${this.selectors.viewExpModal} .loading`).hide("fast");
    $(`${this.selectors.viewExpModal} .details`).slideDown("fast");
    $(`${this.selectors.viewExpModal} .modal-footer`).slideDown("fast");
  }

  /**
   * Populate edit modal with expense details
   */
  populateEditModal(response, expenseId) {
    const describe = response.describe === "N/A" ? "" : response.describe;

    $("#edit_exp_date").val(response.dates_form);
    $("#edit_exp_title").val(response.title);
    $("#edit_exp_amount").val(response.amount_form);
    $("#edit_exp_description").val(describe);
    $(this.selectors.expenseId).val(expenseId);

    $(`${this.selectors.updateExpModal} .loading`).hide("fast");
    $(`${this.selectors.updateExpModal} .exp_form`).slideDown("fast");
    $(`${this.selectors.updateExpModal} .modal-footer`).slideDown("fast");
  }

  /**
   * Fill edit form - handles view, edit, and delete actions
   */
  fillEditForm(id, action) {
    if (action === "edit") {
      $(`${this.selectors.updateExpModal} .exp_form`).hide("fast");
      $(`${this.selectors.updateExpModal} .modal-footer`).hide("fast");
      $(`${this.selectors.updateExpModal} .loading`).show("fast");
      $(this.selectors.updateExpModal).modal("show");
      this.fetchExpenseDetails(id, "edit");
    } else if (action === "view") {
      $(`${this.selectors.viewExpModal} .details`).hide("fast");
      $(`${this.selectors.viewExpModal} .modal-footer`).hide("fast");
      $(`${this.selectors.viewExpModal} .loading`).show("fast");
      $(this.selectors.viewExpModal).modal("show");
      this.fetchExpenseDetails(id, "view");
    } else if (action === "del") {
      $(this.selectors.expenseDelId).val(parseInt(id));
      $(this.selectors.deleteExpModal).modal("show");
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
      url: $(this.selectors.expensesListUrl).val(),
      type: "POST",
      data: (d) => {
        const dateRange = this.getDateRange();
        d.start_date = dateRange.start;
        d.end_date = dateRange.end;
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
      { data: "title" },
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
        targets: [0, 6],
        orderable: false,
      },
      {
        targets: 6,
        createdCell: (cell, cellData, rowData) => {
          const buttons = `
            <button class="btn btn-sm btn-dblue text-white me-1" onclick="expensesManager.fillEditForm(${rowData.id}, 'edit')">
              <i class="fas fa-edit"></i>
            </button>
            <button class="btn btn-sm btn-danger me-1" onclick="expensesManager.fillEditForm(${rowData.id}, 'del')">
              <i class="fas fa-trash"></i>
            </button>
            <button class="btn btn-sm btn-success" onclick="expensesManager.fillEditForm(${rowData.id}, 'view')">
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
        targets: [2, 4, 5],
        createdCell: (cell) => {
          $(cell).removeClass("text-center").addClass("text-start ps-3");
        },
      },
      {
        targets: 3,
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
    const grandTotals = response.json.grand_totals;
    this.updateFooter({ total_amount: grandTotals.total_amount });
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
          $(api.column(colIdx).header()).index()
        );
        cell.addClass("bg-white");

        if (colIdx === 0 || colIdx === 6) {
          cell.html("");
        } else if (colIdx === 1) {
          const calendar = `
            <button type="button" class="btn btn-primary text-white" 
                    data-bs-toggle="modal" data-bs-target="${this.selectors.dateFilterModal}">
              <i class="fas fa-calendar-alt"></i>
            </button>
          `;
          cell.html(calendar).addClass("text-center");
        } else {
          cell
            .html(
              "<input type='text' class='form-control d-inline-block w-auto' placeholder='Filter'/>"
            )
            .addClass("text-center");
          this.setupColumnFilter(cell, api, colIdx);
        }
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
          this.value === ""
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
        dateEnd
      )}`;
    } else if (dateStart) {
      reportDates = `From ${this.formatDates(dateStart)}`;
    } else if (dateEnd) {
      reportDates = `Up to ${this.formatDates(dateEnd)}`;
    }

    const tr = footer.find("tr:eq(0)");
    tr.find("th:eq(1)").text(reportDates);
    tr.find("th:eq(3)").text(totals.total_amount);
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
let expensesManager;
$(function () {
  expensesManager = new ExpensesManager();
});

// Legacy function support for existing onclick handlers
function fill_edit_form(id, str) {
  if (window.expensesManager) {
    window.expensesManager.fillEditForm(id, str);
  }
}
