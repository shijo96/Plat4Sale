/**
 * Plat4Sale - Frontend Dynamic Interactions
 */

document.addEventListener("DOMContentLoaded", function () {
  initSearchAutocomplete();
  initAjaxCart();
  initAjaxWishlist();
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

// Show Toast Alert Notification
function showToast(message, type = "success") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toastEl = document.createElement("div");
  const bgClass = type === "success" ? "bg-dark text-white" : "bg-danger text-white";
  const icon = type === "success" ? "bi-check-circle-fill text-warning" : "bi-exclamation-triangle-fill text-white";

  toastEl.className = `toast align-items-center ${bgClass} border-0 shadow-lg mb-2`;
  toastEl.setAttribute("role", "alert");
  toastEl.setAttribute("aria-live", "assertive");
  toastEl.setAttribute("aria-atomic", "true");
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

    const formData = new FormData();
    formData.append("quantity", "1");

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
        btn.disabled = false;
        btn.innerHTML = originalHtml;
        if (data.success) {
          // Update header badges
          const badge = document.getElementById("header-cart-count");
          if (badge) badge.textContent = data.cart_count;

          const mobileBadge = document.getElementById("mobile-cart-count");
          if (mobileBadge) mobileBadge.textContent = data.cart_count;

          showToast(data.message, "success");
        } else {
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
