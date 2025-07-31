class LipaNambaManager {
  constructor() {
    this.config = {
      columnIndices: [0, 1, 2, 3, 4, 5],
      dateCache: { start: null, end: null },
      csrfToken: this.getCSRFToken(),
      deletingState: false,
    };

    this.selectors = {
      newTransactionForm: "#new_lipa_transaction_form",
      editTransactionForm: "#edit_lipa_transaction_form",
      deleteForm: "#del_lipa_form",
      table: "#lipanamba_table",
      transactionsToggle: "#transactions_toggle",
      searchInput: "#search_lipa_field",
      clearFilter: "#lipanamba_filter_clear",
      minDate: "#min_trans_date",
      maxDate: "#max_trans_date",
      dateClearBtn: "#date_filter_clear",
      dateFilterBtn: "#date_filter_btn",
      pageUrl: "#lipanamba_page_url",

      // Form fields
      lipaNames: "#lipa_names",
      lipaAmount: "#lipa_amount",
      lipaDescription: "#lipa_description",
      lipaEditNames: "#lipa_edit_names",
      lipaEditAmount: "#lipa_edit_amount",
      lipaEditDescription: "#lipa_edit_description",
      transactionId: "#transaction_id",
      lipaDelId: "#lipa_del_id",

      // Buttons
      lipaTransBtn: "#lipa_trans_btn",
      lipaEditTransBtn: "#lipa_edit_trans_btn",
      lipaDeleteBtn: "#lipa_delete_btn",

      // Modals
      updateLipaModal: "#update_lipa_modal",
      deleteLipaModal: "#delete_lipa_modal",
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
    $(this.selectors.transactionsToggle).click();
    this.setupFormHandlers();
    this.setupTable();
    this.setupEventHandlers();
  }

  /**
   * Format dates for display
   */
  formatDates(dateStr, type) {
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

    const dateFormat = `${day}-${
      months[date.getMonth()]
    }-${date.getFullYear()}`;

    return type === "datetime"
      ? `${dateFormat} ${hours}:${minutes}`
      : dateFormat;
  }

  /**
   * Generate alert messages
   */
  generateAlert(isSuccess, message) {
    const iconType = isSuccess ? "check" : "exclamation";
    return `<i class="fas fa-${iconType}-circle"></i> &nbsp; ${message}`;
  }

  /**
   * Setup all form handlers
   */
  setupFormHandlers() {
    this.setupNewTransactionForm();
    this.setupEditTransactionForm();
    this.setupDeleteForm();
  }

  /**
   * Setup new transaction form
   */
  setupNewTransactionForm() {
    $(this.selectors.newTransactionForm).on("submit", (e) => {
      e.preventDefault();
      this.handleNewTransaction();
    });
  }

  /**
   * Setup edit transaction form
   */
  setupEditTransactionForm() {
    $(this.selectors.editTransactionForm).on("submit", (e) => {
      e.preventDefault();
      this.handleEditTransaction();
    });
  }

  /**
   * Setup delete form
   */
  setupDeleteForm() {
    $(this.selectors.deleteForm).on("submit", (e) => {
      e.preventDefault();
      this.handleDeleteTransaction();
    });
  }

  /**
   * Handle new transaction submission
   */
  handleNewTransaction() {
    const formData = new FormData();
    formData.append("names", $.trim($(this.selectors.lipaNames).val()));
    formData.append("amount", $(this.selectors.lipaAmount).val());
    formData.append(
      "describe",
      $.trim($(this.selectors.lipaDescription).val())
    );

    this.submitForm({
      form: this.selectors.newTransactionForm,
      data: formData,
      button: this.selectors.lipaTransBtn,
      buttonText: "Add",
      onSuccess: (response) => {
        if (response.success) {
          $(this.selectors.newTransactionForm)[0].reset();
          this.table.draw();
        }
      },
    });
  }

  /**
   * Handle edit transaction submission
   */
  handleEditTransaction() {
    const formData = new FormData();
    formData.append("transact_id", $(this.selectors.transactionId).val());
    formData.append("names", $.trim($(this.selectors.lipaEditNames).val()));
    formData.append("amount", $(this.selectors.lipaEditAmount).val());
    formData.append(
      "describe",
      $.trim($(this.selectors.lipaEditDescription).val())
    );

    this.submitForm({
      form: this.selectors.editTransactionForm,
      data: formData,
      button: this.selectors.lipaEditTransBtn,
      buttonText: "Update",
      onSuccess: (response) => {
        if (response.success) {
          this.table.draw();
        }
      },
    });
  }

  /**
   * Handle delete transaction submission
   */
  handleDeleteTransaction() {
    const lipaId = $(this.selectors.lipaDelId).val();

    if (parseInt(lipaId) > 0) {
      const formData = new FormData();
      formData.append("delete_id", lipaId);

      this.submitForm({
        form: this.selectors.deleteForm,
        data: formData,
        button: this.selectors.lipaDeleteBtn,
        buttonText: "Yes",
        onSuccess: (response) => {
          if (response.success) {
            $(this.selectors.lipaDelId).val("");
            this.table.draw();
          }
        },
      });
    }
  }

  /**
   * Generic form submission handler
   */
  submitForm({ form, data, button, buttonText, onSuccess }) {
    const formSms = $(`${form} .formsms`);
    const submitBtn = $(button);

    $.ajax({
      type: "POST",
      url: $(form).attr("action"),
      data: data,
      dataType: "json",
      contentType: false,
      processData: false,
      headers: { "X-CSRFToken": this.config.csrfToken },
      beforeSend: () => {
        submitBtn
          .html("<i class='fas fa-spinner fa-pulse'></i>")
          .attr("type", "button");
      },
      success: (response) => {
        submitBtn.html(buttonText).attr("type", "submit");

        const alert = this.generateAlert(response.success, response.sms);
        const alertClass = response.success ? "alert-success" : "alert-danger";
        const removeClass = response.success ? "alert-danger" : "alert-success";

        formSms
          .removeClass(removeClass)
          .addClass(alertClass)
          .html(alert)
          .slideDown("fast")
          .delay(5000)
          .slideUp("fast");

        if (onSuccess) {
          onSuccess(response);
        }
      },
      error: (xhr, status, error) => {
        console.error(error);
        submitBtn.html(buttonText).attr("type", "submit");
      },
    });
  }

  /**
   * Fill edit/delete form with data
   */
  fillEditForm(rowIndex, id, action) {
    if (action === "edit") {
      const row = $(
        `${this.selectors.table} tbody tr:nth-child(${rowIndex + 1})`
      );
      const amount = $("td:nth-child(4)", row).text().replace(/,/g, "");
      let describe = $("td:nth-child(1)", row).attr("data-bs-describe");
      describe = describe === "null" ? "" : describe;

      $(this.selectors.lipaEditNames).val($("td:nth-child(3)", row).text());
      $(this.selectors.lipaEditAmount).val(parseFloat(amount));
      $(this.selectors.lipaEditDescription).val(describe);
      $(this.selectors.transactionId).val(id);
      $(this.selectors.updateLipaModal).modal("show");
    } else {
      $(this.selectors.lipaDelId).val(id);
      $(this.selectors.deleteLipaModal).modal("show");
    }
  }

  /**
   * Get date range for filtering
   */
  getDateRange() {
    const minDateStr = $(this.selectors.minDate).val();
    const maxDateStr = $(this.selectors.maxDate).val();

    try {
      let dtStartUtc = null;
      let dtEndUtc = null;

      if (minDateStr) {
        const startDateLocal = new Date(`${minDateStr}T00:00:00.000`);
        if (isNaN(startDateLocal.getTime())) {
          throw new Error("Invalid start date format");
        }
        dtStartUtc = startDateLocal.toISOString();
      }

      if (maxDateStr) {
        const endDateLocal = new Date(`${maxDateStr}T23:59:59.999`);
        if (isNaN(endDateLocal.getTime())) {
          throw new Error("Invalid end date format");
        }
        dtEndUtc = endDateLocal.toISOString();
      }

      // Cache the results
      this.config.dateCache.start = dtStartUtc;
      this.config.dateCache.end = dtEndUtc;

      return { start: dtStartUtc, end: dtEndUtc };
    } catch (error) {
      console.error("Date processing error:", error);
      return { start: null, end: null };
    }
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
      url: $(this.selectors.pageUrl).val(),
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
      { data: "names" },
      { data: "amount" },
      { data: "profit" },
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
        createdCell: (cell, cellData, rowData, rowIndex) => {
          const btn = `
            <button class="btn btn-sm btn-dblue text-white me-1" 
                    onclick="lipaNambaManager.fillEditForm(${rowIndex}, ${rowData.id}, 'edit')">
              <i class="fas fa-edit"></i>
            </button>
            <button class="btn btn-sm btn-danger" 
                    onclick="lipaNambaManager.fillEditForm('', ${rowData.id}, 'del')">
              <i class="fas fa-trash"></i>
            </button>
          `;
          $(cell).html(btn);
        },
      },
      {
        targets: 0,
        createdCell: (cell, cellData, rowData) => {
          const info = rowData.describe === "" ? "null" : rowData.describe;
          $(cell)
            .attr("data-bs-toggle", "tooltip")
            .attr("title", "Comment: " + info)
            .attr("data-bs-describe", info);
        },
      },
      {
        targets: "_all",
        className: "align-middle text-nowrap text-center",
      },
    ];
  }

  /**
   * Handle draw callback
   */
  handleDrawCallback(response) {
    const grandTotals = response.json.grand_totals;
    const grandObj = {
      total_amount: grandTotals.total_amount,
      total_profit: grandTotals.total_profit,
    };
    this.updateFooter(grandObj);
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

        if (colIdx === 0 || colIdx === 5) {
          cell.html("");
        } else if (colIdx === 1) {
          const calendar = `
            <button type="button" class="btn btn-primary text-white" 
                    data-bs-toggle="modal" data-bs-target="#dateFilterModal">
              <i class="fas fa-calendar-alt"></i>
            </button>
          `;
          cell.html(calendar).addClass("text-center");
        } else {
          cell
            .html(
              "<input type='text' class='text-charcoal' placeholder='Filter..'/>"
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

    $(this.selectors.dateClearBtn)
      .off("click")
      .on("click", () => this.clearDates());

    $(this.selectors.dateFilterBtn)
      .off("click")
      .on("click", () => this.table.draw());
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
      reportDates = `${this.formatDates(
        dateStart,
        "date"
      )} - ${this.formatDates(dateEnd, "date")}`;
    } else if (dateStart) {
      reportDates = `From ${this.formatDates(dateStart, "date")}`;
    } else if (dateEnd) {
      reportDates = `Up to ${this.formatDates(dateEnd, "date")}`;
    }

    const tr = footer.find("tr:eq(0)");
    tr.find("th:eq(1)").text(reportDates);
    tr.find("th:eq(3)").text(totals.total_amount);
    tr.find("th:eq(4)").text(totals.total_profit);
  }
}

// Global reference for onclick handlers
let lipaNambaManager;

// Initialize the application when DOM is ready
$(function () {
  lipaNambaManager = new LipaNambaManager();
});

// Global function for backward compatibility with onclick handlers
function fill_edit_form(rowIndex, id, str) {
  if (lipaNambaManager) {
    lipaNambaManager.fillEditForm(rowIndex, id, str);
  }
}
