class AuthManager {
  constructor() {
    this.config = {
      csrfToken: this.getCSRFToken(),
      urlParams: new URLSearchParams(window.location.search),
    };

    this.selectors = {
      loginForm: "#login_form",
      submitBtn: "#auth_submit_button",
      formSms: "#login_form .formsms",
    };

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
    this.setupFormHandler();
  }

  /**
   * Generate alert messages
   */
  generateAlert(isSuccess, message) {
    const alertType = isSuccess ? "success" : "danger";
    const iconType = isSuccess ? "check" : "exclamation";

    return `
      <div class="alert alert-${alertType} alert-dismissible fade show px-2 m-0 d-block w-100">
        <i class='fas fa-${iconType}-circle'></i> ${message}
        <button type="button" class="btn-close d-inline-block" data-bs-dismiss="alert"></button>
      </div>
    `;
  }

  /**
   * Setup form submission handler
   */
  setupFormHandler() {
    $(this.selectors.loginForm).on("submit", (e) => this.handleFormSubmit(e));
  }

  /**
   * Handle form submission
   */
  handleFormSubmit(e) {
    e.preventDefault();
    const form = $(this.selectors.loginForm);
    const formData = new FormData(form[0]);

    // Append next URL if present
    if (this.config.urlParams.has("next")) {
      formData.append("next_url", this.config.urlParams.get("next"));
    }

    $.ajax({
      type: "POST",
      url: form.attr("action"),
      data: formData,
      dataType: "json",
      contentType: false,
      processData: false,
      headers: { "X-CSRFToken": this.config.csrfToken },
      beforeSend: () => this.setFormLoading(true),
      success: (response) => this.handleFormSuccess(response),
      error: () => this.handleFormError(),
    });
  }

  /**
   * Set form loading state
   */
  setFormLoading(isLoading) {
    const submitBtn = $(this.selectors.submitBtn);

    if (isLoading) {
      submitBtn
        .html("<i class='fas fa-spinner fa-pulse'></i>")
        .attr("type", "button");
    } else {
      submitBtn
        .html("<i class='fas fa-sign-in-alt me-2'></i>Login")
        .attr("type", "submit");
    }
  }

  /**
   * Handle form success response
   */
  handleFormSuccess(response) {
    if (response.success) {
      window.location.href = response.url;
    } else {
      this.setFormLoading(false);
      const feedback = this.generateAlert(response.success, response.sms);
      $(this.selectors.formSms).html(feedback).show();
    }
  }

  /**
   * Handle form error
   */
  handleFormError() {
    this.setFormLoading(false);
    const feedback = this.generateAlert(false, "Unknown error.");
    $(this.selectors.formSms).html(feedback).show();
  }
}

// Initialize the application when DOM is ready
$(function () {
  new AuthManager();
});
