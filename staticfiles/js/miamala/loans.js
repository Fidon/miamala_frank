class LoansManager {
  constructor() {
    this.config = {
      columnIndices: [0, 1, 2, 3, 4, 5, 6],
      dateCache: { start: null, end: null },
      csrfToken: this.getCSRFToken(),
      deletingState: false,
    };

    this.selectors = {
      newLoanForm: "#new_loan_form",
      editLoanForm: "#edit_loan_form",
      deleteLoanForm: "#del_loan_form",
      loansTable: "#loans_table",
      searchField: "#search_loan_field",
      filterClear: "#loans_filter_clear",
      minDate: "#min_loan_date",
      maxDate: "#max_loan_date",
      dateClear: "#date_filter_clear",
      dateFilterBtn: "#date_filter_btn",
      loansPageUrl: "#loans_page_url",
      transactionsToggle: "#transactions_toggle",
      updateLoanModal: "#update_loan_modal",
      deleteLoanModal: "#delete_loan_modal",
      dateFilterModal: "#dateFilterModal",
      // Form fields
      loanNames: "#loan_names",
      loanAmount: "#loan_amount",
      loanDescription: "#loan_description",
      loanEditNames: "#loan_edit_names",
      loanEditAmount: "#loan_edit_amount",
      loanEditPaid: "#loan_edit_paid",
      loanEditDescription: "#loan_edit_description",
      loanId: "#loan_id",
      loanDelId: "#loan_del_id",
      // Buttons
      newLoanBtn: "#new_loan_btn",
      loanEditBtn: "#loan_edit_btn",
      loanDeleteBtn: "#loan_delete_btn",
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
  formatDates(dateStr, str) {
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

    const day = date.getDate() < 10 ? "0" + date.getDate() : date.getDate();
    const hours =
      date.getHours() < 10 ? "0" + date.getHours() : date.getHours();
    const minutes =
      date.getMinutes() < 10 ? "0" + date.getMinutes() : date.getMinutes();

    if (str === "datetime") {
      return `${day}-${
        months[date.getMonth()]
      }-${date.getFullYear()} ${hours}:${minutes}`;
    }
    return `${day}-${months[date.getMonth()]}-${date.getFullYear()}`;
  }

  /**
   * Check if loan payment is valid
   */
  checkLoan(loan, paid) {
    if (paid < 0) {
      return Math.abs(paid) <= loan;
    }
    return true;
  }

  /**
   * Generate alert messages
   */
  generateAlert(isSuccess, message) {
    const iconType = isSuccess ? "check" : "exclamation";
    const alertClass = isSuccess ? "alert-success" : "alert-danger";

    return `<i class="fas fa-${iconType}-circle"></i> &nbsp; ${message}`;
  }

  /**
   * Display form message
   */
  showFormMessage(selector, isSuccess, message) {
    const formSms = $(`${selector} .formsms`);
    const alert = this.generateAlert(isSuccess, message);

    formSms
      .removeClass("alert-success alert-danger")
      .addClass(isSuccess ? "alert-success" : "alert-danger")
      .html(alert)
      .slideDown("fast")
      .delay(2000)
      .slideUp("fast");
  }

  /**
   * Set button loading state
   */
  setButtonLoading(buttonSelector, isLoading, originalText = "Submit") {
    const button = $(buttonSelector);

    if (isLoading) {
      button
        .html("<i class='fas fa-spinner fa-pulse'></i>")
        .attr("type", "button");
    } else {
      button.html(originalText).attr("type", "submit");
    }
  }

  /**
   * Setup all form handlers
   */
  setupFormHandlers() {
    this.setupNewLoanForm();
    this.setupEditLoanForm();
    this.setupDeleteLoanForm();
  }

  /**
   * Setup new loan form
   */
  setupNewLoanForm() {
    $(this.selectors.newLoanForm).on("submit", (e) => {
      e.preventDefault();

      const formData = new FormData();
      formData.append("names", $.trim($(this.selectors.loanNames).val()));
      formData.append("amount", $(this.selectors.loanAmount).val());
      formData.append(
        "describe",
        $.trim($(this.selectors.loanDescription).val())
      );

      $.ajax({
        type: "POST",
        url: $(this.selectors.newLoanForm).attr("action"),
        data: formData,
        dataType: "json",
        contentType: false,
        processData: false,
        headers: { "X-CSRFToken": this.config.csrfToken },
        beforeSend: () =>
          this.setButtonLoading(this.selectors.newLoanBtn, true),
        success: (response) => this.handleNewLoanSuccess(response),
        error: (xhr, status, error) => {
          console.error(error);
          this.setButtonLoading(this.selectors.newLoanBtn, false, "Add");
        },
      });
    });
  }

  /**
   * Handle new loan form success
   */
  handleNewLoanSuccess(response) {
    this.setButtonLoading(this.selectors.newLoanBtn, false, "Add");
    this.showFormMessage(
      this.selectors.newLoanForm,
      response.success,
      response.sms
    );

    if (response.success) {
      $(this.selectors.newLoanForm)[0].reset();
      this.table.draw();
    }
  }

  /**
   * Setup edit loan form
   */
  setupEditLoanForm() {
    $(this.selectors.editLoanForm).on("submit", (e) => {
      e.preventDefault();

      const loanAmount = parseFloat($(this.selectors.loanEditAmount).val());
      const loanPaid = parseFloat($(this.selectors.loanEditPaid).val());

      if (!this.checkLoan(loanAmount, loanPaid)) {
        this.showFormMessage(
          this.selectors.editLoanForm,
          false,
          "Paid amount cannot exceed current loan!"
        );
        return;
      }

      const formData = new FormData();
      formData.append("loan_id", $(this.selectors.loanId).val());
      formData.append("names", $.trim($(this.selectors.loanEditNames).val()));
      formData.append("paid", loanPaid);
      formData.append(
        "describe",
        $.trim($(this.selectors.loanEditDescription).val())
      );

      $.ajax({
        type: "POST",
        url: $(this.selectors.editLoanForm).attr("action"),
        data: formData,
        dataType: "json",
        contentType: false,
        processData: false,
        headers: { "X-CSRFToken": this.config.csrfToken },
        beforeSend: () =>
          this.setButtonLoading(this.selectors.loanEditBtn, true),
        success: (response) =>
          this.handleEditLoanSuccess(response, loanAmount, loanPaid),
        error: (xhr, status, error) => {
          console.error(error);
          this.setButtonLoading(this.selectors.loanEditBtn, false, "Update");
        },
      });
    });
  }

  /**
   * Handle edit loan form success
   */
  handleEditLoanSuccess(response, loanAmount, loanPaid) {
    this.setButtonLoading(this.selectors.loanEditBtn, false, "Update");
    this.showFormMessage(
      this.selectors.editLoanForm,
      response.success,
      response.sms
    );

    if (response.success) {
      $(this.selectors.loanEditAmount).val(loanAmount + loanPaid);
      $(this.selectors.loanEditPaid).val("");
      this.table.draw();
    }
  }

  /**
   * Setup delete loan form
   */
  setupDeleteLoanForm() {
    $(this.selectors.deleteLoanForm).on("submit", (e) => {
      e.preventDefault();

      const delLoanId = $(this.selectors.loanDelId).val();
      if (parseInt(delLoanId) <= 0) return;

      const formData = new FormData();
      formData.append("delete_id", delLoanId);

      $.ajax({
        type: "POST",
        url: $(this.selectors.deleteLoanForm).attr("action"),
        data: formData,
        dataType: "json",
        contentType: false,
        processData: false,
        headers: { "X-CSRFToken": this.config.csrfToken },
        beforeSend: () =>
          this.setButtonLoading(this.selectors.loanDeleteBtn, true),
        success: (response) => this.handleDeleteLoanSuccess(response),
        error: (xhr, status, error) => {
          console.error(error);
          this.setButtonLoading(this.selectors.loanDeleteBtn, false, "Yes");
        },
      });
    });
  }

  /**
   * Handle delete loan form success
   */
  handleDeleteLoanSuccess(response) {
    this.setButtonLoading(this.selectors.loanDeleteBtn, false, "Yes");
    this.showFormMessage(
      this.selectors.deleteLoanForm,
      response.success,
      response.sms
    );

    if (response.success) {
      $(this.selectors.loanDelId).val("");
      this.table.draw();
    }
  }

  /**
   * Fill edit form with data
   */
  fillEditForm(rowIndex, id, action) {
    if (action === "edit") {
      const row = $(
        `${this.selectors.loansTable} tbody tr:nth-child(${rowIndex + 1})`
      );
      const names = $("td:nth-child(3)", row).text();
      const loan = $("td:nth-child(6)", row).text().replace(/,/g, "");
      let describe = $("td:nth-child(1)", row).attr("data-bs-describe");
      describe = describe === "null" ? "" : describe;

      $(this.selectors.loanEditNames).val(names);
      $(this.selectors.loanEditAmount).val(parseFloat(loan));
      $(this.selectors.loanEditDescription).val(describe);
      $(this.selectors.loanId).val(id);
      $(this.selectors.updateLoanModal).modal("show");
    } else {
      $(this.selectors.loanDelId).val(id);
      $(this.selectors.deleteLoanModal).modal("show");
    }
  }

  /**
   * Date range management
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
    $(`${this.selectors.loansTable} thead tr`)
      .clone(true)
      .attr("class", "filters")
      .appendTo(`${this.selectors.loansTable} thead`);

    this.table = $(this.selectors.loansTable).DataTable({
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
      url: $(this.selectors.loansPageUrl).val(),
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
      { data: "paid" },
      { data: "balance" },
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
        createdCell: (cell, cellData, rowData, rowIndex) => {
          const btn = `
            <button class="btn btn-sm btn-dblue text-white me-1" 
                    onclick="loansManager.fillEditForm(${rowIndex}, ${rowData.id}, 'edit')">
              <i class="fas fa-edit"></i>
            </button> 
            <button class="btn btn-sm btn-danger" 
                    onclick="loansManager.fillEditForm('', ${rowData.id}, 'del')">
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
   * Handle table draw callback
   */
  handleDrawCallback(response) {
    const grandTotals = response.json.grand_totals;
    this.updateFooter({
      total_amount: grandTotals.total_amount,
      total_paid: grandTotals.total_paid,
      total_balance: grandTotals.total_balance,
    });
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
    $(this.selectors.searchField)
      .off("keyup")
      .on("keyup", () => {
        this.table.search($(this.selectors.searchField).val()).draw();
      });
  }

  /**
   * Setup filter handlers
   */
  setupFilterHandlers() {
    $(this.selectors.filterClear)
      .off("click")
      .on("click", (e) => {
        e.preventDefault();
        $(this.selectors.searchField).val("");
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
    tr.find("th:eq(4)").text(totals.total_paid);
    tr.find("th:eq(5)").text(totals.total_balance);
  }
}

// Initialize the application when DOM is ready
let loansManager;
$(function () {
  loansManager = new LoansManager();
});

// Global functions for backward compatibility with onclick handlers
function fill_edit_form(rowIndex, id, str) {
  loansManager.fillEditForm(rowIndex, id, str);
}
