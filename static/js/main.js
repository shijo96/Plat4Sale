/**
 * Plat4Sale - Frontend Dynamic Interactions & SweetAlert2 Integration
 */

document.addEventListener("DOMContentLoaded", function () {
  initSearchAutocomplete();
  initAjaxCart();
  initAjaxWishlist();
  initSweetConfirmInterceptors();
  initProductClickTracking();
});

// CSRF Helper for AJAX requests
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// SweetAlert2 Styled Notification Toast
function showToast(message, type = "success") {
  if (typeof Swal !== "undefined") {
    const icon = (type === "danger" || type === "error") ? "error" : type;
    Swal.fire({
      toast: true,
      position: "top-end",
      icon: icon,
      title: message,
      showConfirmButton: false,
      timer: 3500,
      timerProgressBar: true,
      backdrop: false,
      customClass: {
        popup: `plat-swal-toast plat-swal-${icon}`,
      },
      didOpen: (toast) => {
        toast.addEventListener("mouseenter", Swal.stopTimer);
        toast.addEventListener("mouseleave", Swal.resumeTimer);
      },
    });
    return;
  }

  // Fallback to Bootstrap toast if SweetAlert is loading
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toastEl = document.createElement("div");
  const bgClass = type === "success" ? "bg-dark text-white" : "bg-danger text-white";
  const icon = type === "success" ? "bi-check-circle-fill text-warning" : "bi-exclamation-triangle-fill text-white";

  toastEl.className = `toast align-items-center ${bgClass} border-0 shadow-lg mb-2`;
  toastEl.innerHTML = `
    <div class="d-flex">
      <div class="toast-body d-flex align-items-center gap-2">
        <i class="bi ${icon} fs-5"></i>
        <span>${message}</span>
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
  `;
  container.appendChild(toastEl);
  const bsToast = new bootstrap.Toast(toastEl, { delay: 3500 });
  bsToast.show();
  toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
}

// Plat4Sale - SweetAlert2 Theme Cleaner (Styles are managed via static/css/main.css)
function injectSweetAlertTheme() {
  const stale = document.getElementById("plat-swal-theme-injected");
  if (stale) {
    stale.remove();
  }
}

if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", injectSweetAlertTheme);
  } else {
    injectSweetAlertTheme();
  }
}

// Automatically override standard window.alert with SweetAlert2
if (typeof window !== "undefined") {
  window.originalAlert = window.alert;
  window.alert = function (message) {
    if (typeof Swal !== "undefined") {
      injectSweetAlertTheme();
      return Swal.fire({
        title: "Notice",
        text: String(message),
        icon: "info",
        confirmButtonText: "Got It",
      });
    } else if (window.originalAlert) {
      window.originalAlert(message);
    }
  };
}

// Global SweetAlert Helpers
window.sweetAlert = function (title, text, icon = "info") {
  injectSweetAlertTheme();
  if (typeof Swal !== "undefined") {
    return Swal.fire({
      title: title,
      text: text,
      icon: icon,
      confirmButtonText: "Got It",
    });
  }
  alert(`${title}\n\n${text}`);
};

window.sweetConfirm = function (title, text, confirmBtnText = "Yes, Proceed", icon = "warning", isDanger = true) {
  injectSweetAlertTheme();
  if (typeof Swal !== "undefined") {
    return Swal.fire({
      title: title,
      text: text,
      icon: icon,
      showCancelButton: true,
      confirmButtonText: confirmBtnText,
      cancelButtonText: "Cancel",
      reverseButtons: true,
      customClass: {
        confirmButton: isDanger ? "swal2-danger plat-btn-danger" : "",
      },
    });
  }
  return Promise.resolve({ isConfirmed: confirm(`${title}\n\n${text}`) });
};

// Universal SweetAlert Confirmation Interceptor for Forms & Links
function initSweetConfirmInterceptors() {
  injectSweetAlertTheme();

  // Forms with data-confirm
  document.addEventListener("submit", function (e) {
    const form = e.target;
    const submitter = e.submitter;
    const confirmMsg = form.getAttribute("data-confirm") || (submitter && submitter.getAttribute("data-confirm"));
    if (confirmMsg && !form.dataset.confirmed) {
      e.preventDefault();
      if (typeof Swal !== "undefined") {
        injectSweetAlertTheme();
        const title = form.getAttribute("data-confirm-title") || (submitter && submitter.getAttribute("data-confirm-title")) || "Are you sure?";
        const btnText = form.getAttribute("data-confirm-btn") || (submitter && submitter.getAttribute("data-confirm-btn")) || "Yes, Proceed";
        const isDanger = !form.getAttribute("data-confirm-btn-type") || form.getAttribute("data-confirm-btn-type") === "danger" || /delete|cancel|remove|empty/i.test(title + " " + btnText);
        
        Swal.fire({
          title: title,
          text: confirmMsg,
          icon: form.getAttribute("data-confirm-icon") || (submitter && submitter.getAttribute("data-confirm-icon")) || "warning",
          showCancelButton: true,
          confirmButtonText: btnText,
          cancelButtonText: "Cancel",
          reverseButtons: true,
          customClass: {
            confirmButton: isDanger ? "swal2-danger plat-btn-danger" : "",
          },
        }).then((result) => {
          if (result.isConfirmed) {
            form.dataset.confirmed = "true";
            if (typeof form.requestSubmit === "function" && submitter) {
              form.requestSubmit(submitter);
            } else if (typeof form.requestSubmit === "function") {
              form.requestSubmit();
            } else {
              HTMLFormElement.prototype.submit.call(form);
            }
          }
        });
      } else {
        if (confirm(confirmMsg)) {
          form.dataset.confirmed = "true";
          HTMLFormElement.prototype.submit.call(form);
        }
      }
    }
  });

  // Action links / buttons with data-confirm
  document.addEventListener("click", function (e) {
    const trigger = e.target.closest("a[data-confirm], button[data-confirm]:not([type='submit'])");
    if (!trigger || trigger.dataset.confirmed) return;

    e.preventDefault();
    const confirmMsg = trigger.getAttribute("data-confirm");
    if (typeof Swal !== "undefined") {
      injectSweetAlertTheme();
      const title = trigger.getAttribute("data-confirm-title") || "Are you sure?";
      const btnText = trigger.getAttribute("data-confirm-btn") || "Yes, Proceed";
      const isDanger = !trigger.getAttribute("data-confirm-btn-type") || trigger.getAttribute("data-confirm-btn-type") === "danger" || /delete|cancel|remove|empty/i.test(title + " " + btnText);

      Swal.fire({
        title: title,
        text: confirmMsg,
        icon: trigger.getAttribute("data-confirm-icon") || "warning",
        showCancelButton: true,
        confirmButtonText: btnText,
        cancelButtonText: "Cancel",
        reverseButtons: true,
        customClass: {
          confirmButton: isDanger ? "swal2-danger plat-btn-danger" : "",
        },
      }).then((result) => {
        if (result.isConfirmed) {
          trigger.dataset.confirmed = "true";
          if (trigger.tagName.toLowerCase() === "a") {
            window.location.href = trigger.href;
          } else if (trigger.form) {
            trigger.form.submit();
          } else {
            trigger.click();
          }
        }
      });
    } else {
      if (confirm(confirmMsg)) {
        trigger.dataset.confirmed = "true";
        if (trigger.tagName.toLowerCase() === "a") {
          window.location.href = trigger.href;
        }
      }
    }
  });
}

// Live Search Autocomplete
function initSearchAutocomplete() {
  const searchInput = document.getElementById("main-search-input");
  const resultsDropdown = document.getElementById("search-results-dropdown");
  if (!searchInput || !resultsDropdown) return;

  let debounceTimer;

  searchInput.addEventListener("input", function () {
    clearTimeout(debounceTimer);
    const query = this.value.trim();

    if (query.length < 2) {
      resultsDropdown.style.display = "none";
      resultsDropdown.innerHTML = "";
      return;
    }

    debounceTimer = setTimeout(() => {
      fetch(`/api/search-suggest/?q=${encodeURIComponent(query)}`)
        .then((res) => res.json())
        .then((data) => {
          if (data.results && data.results.length > 0) {
            let html = "";
            data.results.forEach((item) => {
              html += `
                <a href="${item.url}" class="search-result-item">
                  <img src="${item.image}" alt="${item.name}" class="search-result-img" />
                  <div class="flex-grow-1">
                    <div class="fw-bold small text-truncate" style="max-width: 320px;">${item.name}</div>
                    <div class="d-flex align-items-center gap-2 mt-1">
                      <span class="text-danger fw-bold small">${item.price}</span>
                      ${item.original_price ? `<span class="text-muted text-decoration-line-through small" style="font-size:0.75rem;">${item.original_price}</span>` : ""}
                      <span class="badge bg-light text-secondary border" style="font-size:0.65rem;">${item.category}</span>
                    </div>
                  </div>
                  <i class="bi bi-chevron-right text-muted small"></i>
                </a>
              `;
            });
            html += `
              <div class="p-2 text-center bg-light border-top">
                <a href="/products/?q=${encodeURIComponent(query)}" class="small fw-bold text-dark text-decoration-none">
                  View all results for "${query}" →
                </a>
              </div>
            `;
            resultsDropdown.innerHTML = html;
            resultsDropdown.style.display = "block";
          } else {
            resultsDropdown.innerHTML = `
              <div class="p-3 text-center text-muted small">
                No matching products found for "${query}"
              </div>
            `;
            resultsDropdown.style.display = "block";
          }
        })
        .catch(() => {
          resultsDropdown.style.display = "none";
        });
    }, 250);
  });

  // Hide dropdown on click outside
  document.addEventListener("click", function (e) {
    if (!searchInput.contains(e.target) && !resultsDropdown.contains(e.target)) {
      resultsDropdown.style.display = "none";
    }
  });
}

// AJAX Add to Cart
function initAjaxCart() {
  document.addEventListener("click", function (e) {
    const btn = e.target.closest(".ajax-add-cart-btn");
    if (!btn) return;

    e.preventDefault();
    const productId = btn.getAttribute("data-product-id");
    const originalHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Adding...`;

    // Check if variant selections exist on page (e.g., detail page)
    const formData = new FormData();
    const sizeInput = document.querySelector('input[name="size"]:checked');
    const colorInput = document.querySelector('input[name="color"]:checked');
    const qtyInput = document.querySelector('input[name="quantity"]');

    formData.append("quantity", qtyInput ? qtyInput.value : "1");
    if (sizeInput) formData.append("size", sizeInput.value);
    if (colorInput) formData.append("color", colorInput.value);

    fetch(`/cart/add/${productId}/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
        "X-Requested-With": "XMLHttpRequest",
      },
      body: formData,
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          // Update header badges
          const badge = document.getElementById("header-cart-count");
          if (badge) badge.textContent = data.cart_count;

          const mobileBadge = document.getElementById("mobile-cart-count");
          if (mobileBadge) mobileBadge.textContent = data.cart_count;

          showToast(data.message, "success");

          // Transform all add-to-cart buttons for this product into "Go to Cart" buttons
          document.querySelectorAll(`.ajax-add-cart-btn[data-product-id="${productId}"]`).forEach((b) => {
            const isSmall = b.classList.contains("btn-sm");
            const goCartLink = document.createElement("a");
            goCartLink.href = "/cart/";
            goCartLink.className = `btn btn-in-cart ${isSmall ? 'btn-sm' : ''} w-100`;
            goCartLink.innerHTML = `<i class="bi bi-check-circle-fill text-white"></i> In Cart · Go to Cart →`;
            b.replaceWith(goCartLink);
          });
        } else {
          btn.disabled = false;
          btn.innerHTML = originalHtml;
          showToast(data.message || "Could not add product.", "danger");
        }
      })
      .catch(() => {
        btn.disabled = false;
        btn.innerHTML = originalHtml;
        showToast("Error adding item to cart", "danger");
      });
  });
}

// AJAX Wishlist Toggle
function initAjaxWishlist() {
  document.addEventListener("click", function (e) {
    const btn = e.target.closest(".ajax-wishlist-toggle");
    if (!btn) return;

    e.preventDefault();
    const productId = btn.getAttribute("data-product-id");

    fetch(`/wishlist/toggle/${productId}/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then((res) => {
        if (res.status === 401 || res.redirected) {
          window.location.href = `/accounts/login/?next=${window.location.pathname}`;
          return;
        }
        return res.json();
      })
      .then((data) => {
        if (!data) return;
        if (data.success) {
          if (data.added) {
            btn.classList.add("active");
            btn.innerHTML = `<i class="bi bi-heart-fill text-danger"></i>`;
            showToast(data.message, "success");
          } else {
            btn.classList.remove("active");
            btn.innerHTML = `<i class="bi bi-heart"></i>`;
            showToast(data.message, "info");
          }

          const badge = document.getElementById("header-wishlist-count");
          if (badge) badge.textContent = data.wishlist_count;
        }
      })
      .catch(() => {
        showToast("Please log in to manage your wishlist.", "danger");
      });
  });
}

// Product Click & Traffic Tracking
function initProductClickTracking() {
  document.addEventListener("click", function (e) {
    const card = e.target.closest(".product-card[data-product-id]");
    if (!card) return;

    // Ignore wishlist toggle or add-to-cart clicks
    if (
      e.target.closest(".wishlist-toggle-btn") ||
      e.target.closest(".btn-add-cart") ||
      e.target.closest(".btn-in-cart")
    ) {
      return;
    }

    const productId = card.getAttribute("data-product-id");
    if (!productId) return;

    const trackUrl = `/api/track-click/${productId}/`;
    if (navigator.sendBeacon) {
      navigator.sendBeacon(trackUrl);
    } else {
      fetch(trackUrl, {
        method: "POST",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
      }).catch(() => {});
    }
  });
}
