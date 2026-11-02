/**
 * CiviNexa AI - Client-Side Interactive Engine
 * File: static/js/script.js
 * Handles Leaflet Maps, Live AI Classification, Previews, Search Filters & Chart.js
 */

document.addEventListener("DOMContentLoaded", function () {
  // Initialize Tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Setup Image Preview Handler
  setupImagePreview();

  // Setup Live AI Classifier on Report page
  setupAIClassifier();

  // Setup Admin Table Live Search
  setupTableFilter();
});

/**
 * Image Upload Preview
 */
function setupImagePreview() {
  const imageInput = document.getElementById("complaintImage");
  const previewContainer = document.getElementById("imagePreviewContainer");
  const previewImg = document.getElementById("imagePreview");

  if (imageInput && previewContainer && previewImg) {
    imageInput.addEventListener("change", function () {
      const file = this.files[0];
      if (file) {
        // Validate file type
        const validTypes = ["image/jpeg", "image/png", "image/jpg", "image/webp"];
        if (!validTypes.includes(file.type)) {
          alert("Please upload a valid image file (PNG, JPG, JPEG, WEBP).");
          this.value = "";
          previewContainer.classList.add("d-none");
          return;
        }

        // Validate size (max 8MB)
        if (file.size > 8 * 1024 * 1024) {
          alert("Image file size exceeds 8MB limit. Please select a smaller photo.");
          this.value = "";
          previewContainer.classList.add("d-none");
          return;
        }

        const reader = new FileReader();
        reader.onload = function (e) {
          previewImg.src = e.target.result;
          previewContainer.classList.remove("d-none");
        };
        reader.readAsDataURL(file);
      } else {
        previewContainer.classList.add("d-none");
      }
    });
  }
}

/**
 * Interactive Leaflet Map for Complaint Reporting
 */
let reportMap, reportMarker;

function initReportMap(defaultLat = 12.9716, defaultLng = 77.5946) {
  const mapElem = document.getElementById("reportMap");
  if (!mapElem) return;

  reportMap = L.map("reportMap").setView([defaultLat, defaultLng], 13);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(reportMap);

  // Set default coordinates in form
  updateCoordinateInputs(defaultLat, defaultLng);

  // Add marker
  reportMarker = L.marker([defaultLat, defaultLng], { draggable: true }).addTo(reportMap);
  reportMarker.bindPopup("<b>Selected Location</b><br>Drag pin or click map to adjust.").openPopup();

  // Marker drag event
  reportMarker.on("dragend", function (e) {
    const pos = e.target.getLatLng();
    updateCoordinateInputs(pos.lat, pos.lng);
    reverseGeocode(pos.lat, pos.lng);
  });

  // Map click event
  reportMap.on("click", function (e) {
    const lat = e.latlng.lat;
    const lng = e.latlng.lng;
    reportMarker.setLatLng([lat, lng]);
    updateCoordinateInputs(lat, lng);
    reverseGeocode(lat, lng);
  });

  // GPS Locate Button
  const gpsBtn = document.getElementById("btnLocateGPS");
  if (gpsBtn) {
    gpsBtn.addEventListener("click", function () {
      if (navigator.geolocation) {
        gpsBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Locating...';
        gpsBtn.disabled = true;

        navigator.geolocation.getCurrentPosition(
          function (position) {
            const userLat = position.coords.latitude;
            const userLng = position.coords.longitude;
            reportMap.setView([userLat, userLng], 16);
            reportMarker.setLatLng([userLat, userLng]);
            updateCoordinateInputs(userLat, userLng);
            reverseGeocode(userLat, userLng);
            gpsBtn.innerHTML = '<i class="bi bi-crosshair me-1"></i>Current GPS Location Found';
            gpsBtn.classList.replace("btn-outline-secondary", "btn-success");
            gpsBtn.disabled = false;
          },
          function (error) {
            alert("Could not retrieve GPS location. Please pinpoint your location on the map manually.");
            gpsBtn.innerHTML = '<i class="bi bi-geo-alt me-1"></i>Use My Current Location';
            gpsBtn.disabled = false;
          },
          { timeout: 10000, enableHighAccuracy: true }
        );
      } else {
        alert("Geolocation is not supported by your browser.");
      }
    });
  }
}

function updateCoordinateInputs(lat, lng) {
  const latInput = document.getElementById("latitude");
  const lngInput = document.getElementById("longitude");
  const coordDisplay = document.getElementById("coordsDisplay");

  if (latInput) latInput.value = parseFloat(lat).toFixed(6);
  if (lngInput) lngInput.value = parseFloat(lng).toFixed(6);
  if (coordDisplay) {
    coordDisplay.innerText = `Lat: ${parseFloat(lat).toFixed(5)}, Lng: ${parseFloat(lng).toFixed(5)}`;
  }
}

function reverseGeocode(lat, lng) {
  const locInput = document.getElementById("locationInput");
  if (!locInput) return;

  // Use Nominatim API for address resolution with polite rate limiting
  fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`)
    .then((response) => response.json())
    .then((data) => {
      if (data && data.display_name) {
        // If user hasn't explicitly entered custom text, populate it
        if (!locInput.value || locInput.getAttribute("data-autofilled") === "true") {
          locInput.value = data.display_name;
          locInput.setAttribute("data-autofilled", "true");
        }
      }
    })
    .catch((err) => {
      console.log("Geocoding lookup notice:", err);
    });
}

/**
 * Interactive Leaflet Map for Tracking View
 */
function initTrackMap(lat, lng, titleText = "Reported Location") {
  const mapElem = document.getElementById("trackMap");
  if (!mapElem) return;

  const latNum = parseFloat(lat) || 12.9716;
  const lngNum = parseFloat(lng) || 77.5946;

  const trackMap = L.map("trackMap").setView([latNum, lngNum], 15);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(trackMap);

  const marker = L.marker([latNum, lngNum]).addTo(trackMap);
  marker.bindPopup(`<b>${titleText}</b><br>Lat: ${latNum.toFixed(4)}, Lng: ${lngNum.toFixed(4)}`).openPopup();
}

/**
 * Live AI Complaint Classifier Assistant
 */
function setupAIClassifier() {
  const descInput = document.getElementById("description");
  const titleInput = document.getElementById("complaint_title");
  const aiBox = document.getElementById("aiSuggestionBox");
  const btnTriggerAI = document.getElementById("btnTriggerAI");
  const categorySelect = document.getElementById("categorySelect");

  if (!descInput || !aiBox) return;

  let debounceTimer = null;

  function runClassification() {
    const description = descInput.value.trim();
    const title = titleInput ? titleInput.value.trim() : "";

    if (description.length < 5 && title.length < 5) {
      aiBox.classList.add("d-none");
      return;
    }

    // Call Flask AI API
    fetch("/api/classify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ description: description, title: title })
    })
      .then((res) => res.json())
      .then((data) => {
        if (data && data.status === "success") {
          const res = data.result;
          aiBox.classList.remove("d-none");

          document.getElementById("aiCategoryText").innerText = res.category;
          document.getElementById("aiDepartmentText").innerText = res.department;
          document.getElementById("aiConfidenceBar").style.width = res.confidence_percent + "%";
          document.getElementById("aiConfidenceText").innerText = res.confidence_percent + "% confidence";
          document.getElementById("aiPriorityText").innerText = res.priority;

          // Handle Apply Suggestion button
          const btnApply = document.getElementById("btnApplyAISuggestion");
          if (btnApply && categorySelect) {
            btnApply.onclick = function () {
              // Try to select option
              for (let i = 0; i < categorySelect.options.length; i++) {
                if (categorySelect.options[i].value === res.category) {
                  categorySelect.selectedIndex = i;
                  categorySelect.classList.add("border-primary", "shadow-sm");
                  break;
                }
              }
              // Also update suggested department input
              const deptInput = document.getElementById("suggestedDepartment");
              if (deptInput) {
                deptInput.value = res.department;
              }
              btnApply.innerHTML = '<i class="bi bi-check2-circle me-1"></i>Applied!';
              setTimeout(() => {
                btnApply.innerHTML = '<i class="bi bi-magic me-1"></i>Apply AI Suggestion';
              }, 2000);
            };
          }
        }
      })
      .catch((err) => {
        console.error("AI Classification Error:", err);
      });
  }

  // Trigger on typing with 500ms debounce
  descInput.addEventListener("input", function () {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(runClassification, 600);
  });

  if (titleInput) {
    titleInput.addEventListener("input", function () {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(runClassification, 600);
    });
  }

  // Manual trigger button
  if (btnTriggerAI) {
    btnTriggerAI.addEventListener("click", runClassification);
  }
}

/**
 * Admin Complaints Table Client-side Search & Filter
 */
function setupTableFilter() {
  const searchInput = document.getElementById("adminTableSearch");
  const statusFilter = document.getElementById("adminStatusFilter");
  const categoryFilter = document.getElementById("adminCategoryFilter");
  const table = document.getElementById("adminComplaintsTable");

  if (!table) return;

  function filterRows() {
    const query = searchInput ? searchInput.value.toLowerCase().trim() : "";
    const selectedStatus = statusFilter ? statusFilter.value : "All";
    const selectedCategory = categoryFilter ? categoryFilter.value : "All";

    const rows = table.querySelectorAll("tbody tr");

    rows.forEach((row) => {
      const text = row.innerText.toLowerCase();
      const rowStatus = row.getAttribute("data-status") || "";
      const rowCategory = row.getAttribute("data-category") || "";

      const matchesSearch = query === "" || text.includes(query);
      const matchesStatus = selectedStatus === "All" || rowStatus === selectedStatus;
      const matchesCategory = selectedCategory === "All" || rowCategory === selectedCategory;

      if (matchesSearch && matchesStatus && matchesCategory) {
        row.style.display = "";
      } else {
        row.style.display = "none";
      }
    });
  }

  if (searchInput) searchInput.addEventListener("input", filterRows);
  if (statusFilter) statusFilter.addEventListener("change", filterRows);
  if (categoryFilter) categoryFilter.addEventListener("change", filterRows);
}
