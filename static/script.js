// Global variables
let statusCheckInterval = null;

// Initialize on page load
document.addEventListener("DOMContentLoaded", function () {
  loadStates();
});

// Load states from API
async function loadStates() {
  showLoading("Loading states...");

  try {
    const response = await fetch("/api/states");
    const data = await response.json();

    if (data.success) {
      const stateSelect = document.getElementById("state");
      stateSelect.innerHTML = '<option value="">Select State</option>';

      data.data.forEach((state) => {
        const option = document.createElement("option");
        option.value = state.name;
        option.textContent = state.name;
        stateSelect.appendChild(option);
      });

      hideLoading();
    } else {
      throw new Error(data.error || "Failed to load states");
    }
  } catch (error) {
    hideLoading();
    showAlert("Error loading states: " + error.message, "danger");
  }
}

// Load districts based on selected state
async function loadDistricts() {
  const stateSelect = document.getElementById("state");
  const districtSelect = document.getElementById("district");
  const complexSelect = document.getElementById("courtComplex");
  const courtSelect = document.getElementById("courtName");

  const selectedState = stateSelect.value;

  if (!selectedState) {
    resetDependentFields([districtSelect, complexSelect, courtSelect]);
    return;
  }

  showLoading("Loading districts...");

  try {
    const response = await fetch(
      `/api/districts/${encodeURIComponent(selectedState)}`
    );
    const data = await response.json();

    if (data.success) {
      districtSelect.innerHTML = '<option value="">Select District</option>';
      data.data.forEach((district) => {
        const option = document.createElement("option");
        option.value = district.name;
        option.textContent = district.name;
        districtSelect.appendChild(option);
      });

      districtSelect.disabled = false;
      resetDependentFields([complexSelect, courtSelect]);
      hideLoading();
    } else {
      throw new Error(data.error || "Failed to load districts");
    }
  } catch (error) {
    hideLoading();
    showAlert("Error loading districts: " + error.message, "danger");
    resetDependentFields([districtSelect, complexSelect, courtSelect]);
  }
}

// Load court complexes based on selected district
async function loadCourtComplexes() {
  const stateSelect = document.getElementById("state");
  const districtSelect = document.getElementById("district");
  const complexSelect = document.getElementById("courtComplex");
  const courtSelect = document.getElementById("courtName");

  const selectedState = stateSelect.value;
  const selectedDistrict = districtSelect.value;

  if (!selectedState || !selectedDistrict) {
    resetDependentFields([complexSelect, courtSelect]);
    return;
  }

  showLoading("Loading court complexes...");

  try {
    const response = await fetch(
      `/api/court-complexes/${encodeURIComponent(
        selectedState
      )}/${encodeURIComponent(selectedDistrict)}`
    );
    const data = await response.json();

    if (data.success) {
      complexSelect.innerHTML =
        '<option value="">Select Court Complex</option>';
      data.data.forEach((complex) => {
        const option = document.createElement("option");
        option.value = complex.name;
        option.textContent = complex.name;
        complexSelect.appendChild(option);
      });

      complexSelect.disabled = false;
      resetDependentFields([courtSelect]);
      hideLoading();
    } else {
      throw new Error(data.error || "Failed to load court complexes");
    }
  } catch (error) {
    hideLoading();
    showAlert("Error loading court complexes: " + error.message, "danger");
    resetDependentFields([complexSelect, courtSelect]);
  }
}

// Load courts based on selected court complex
async function loadCourts() {
  const stateSelect = document.getElementById("state");
  const districtSelect = document.getElementById("district");
  const complexSelect = document.getElementById("courtComplex");
  const courtSelect = document.getElementById("courtName");

  const selectedState = stateSelect.value;
  const selectedDistrict = districtSelect.value;
  const selectedComplex = complexSelect.value;

  if (!selectedState || !selectedDistrict || !selectedComplex) {
    resetDependentFields([courtSelect]);
    return;
  }

  showLoading("Loading courts...");

  try {
    const response = await fetch(
      `/api/courts/${encodeURIComponent(selectedState)}/${encodeURIComponent(
        selectedDistrict
      )}/${encodeURIComponent(selectedComplex)}`
    );
    const data = await response.json();

    if (data.success) {
      courtSelect.innerHTML = '<option value="All Courts">All Courts</option>';
      data.data.forEach((court) => {
        const option = document.createElement("option");
        option.value = court.name;
        option.textContent = court.name;
        courtSelect.appendChild(option);
      });

      courtSelect.disabled = false;
      hideLoading();
    } else {
      throw new Error(data.error || "Failed to load courts");
    }
  } catch (error) {
    hideLoading();
    showAlert("Error loading courts: " + error.message, "danger");
    resetDependentFields([courtSelect]);
  }
}

// Form submission handler
document
  .getElementById("causelistForm")
  .addEventListener("submit", async function (e) {
    e.preventDefault();

    const state = document.getElementById("state").value;
    const district = document.getElementById("district").value;
    const courtComplex = document.getElementById("courtComplex").value;
    const courtName =
      document.getElementById("courtName").value || "All Courts";
    const date = document.getElementById("date").value;

    // Validate form
    if (!state || !district || !courtComplex || !date) {
      showAlert("Please fill all required fields", "warning");
      return;
    }

    // Validate date format
    if (!isValidDate(date)) {
      showAlert("Please enter a valid date in DD-MM-YYYY format", "warning");
      return;
    }

    // Start PDF download
    downloadCauseListPDF({
      state: state,
      district: district,
      court_complex: courtComplex,
      court_name: courtName,
      date: date,
    });
  });

// Download cause list PDF
async function downloadCauseListPDF(downloadData) {
  showProgressSection();
  updateProgress(0, "Starting PDF download from eCourts...");

  try {
    const response = await fetch("/api/download-causelist", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(downloadData),
    });

    const data = await response.json();

    if (data.success) {
      startStatusCheck();
    } else {
      hideProgressSection();
      showAlert(
        "Failed to start download: " + (data.error || "Unknown error"),
        "danger"
      );
    }
  } catch (error) {
    hideProgressSection();
    showAlert("Error starting download: " + error.message, "danger");
  }
}

// Start checking download status
function startStatusCheck() {
  let progress = 0;
  statusCheckInterval = setInterval(() => {
    fetch("/api/status")
      .then((response) => response.json())
      .then((status) => {
        if (status.status === "completed") {
          clearInterval(statusCheckInterval);
          updateProgress(100, "PDF download completed!");

          setTimeout(() => {
            showDownloadResult(status.data);
          }, 1000);
        } else if (status.status === "error") {
          clearInterval(statusCheckInterval);
          updateProgress(0, status.message);
          showAlert(status.message, "danger");
          setTimeout(hideProgressSection, 3000);
        } else if (status.status === "running") {
          progress = Math.min(progress + 10, 90);
          updateProgress(progress, status.message);
        }
      })
      .catch((error) => {
        console.error("Error checking status:", error);
      });
  }, 1000);
}

// Show download result
function showDownloadResult(result) {
  hideProgressSection();

  const resultsSection = document.getElementById("resultsSection");
  const resultTitle = document.getElementById("resultTitle");
  const resultMessage = document.getElementById("resultMessage");
  const downloadLink = document.getElementById("downloadLink");

  if (result.success) {
    resultTitle.innerHTML =
      '<i class="fas fa-check-circle text-success me-2"></i>Download Successful';
    resultMessage.textContent =
      result.message || "Cause list PDF downloaded successfully";
    downloadLink.href = result.download_url;
    downloadLink.style.display = "inline-block";
  } else {
    resultTitle.innerHTML =
      '<i class="fas fa-times-circle text-danger me-2"></i>Download Failed';
    resultMessage.textContent = result.error || "Failed to download PDF";
    downloadLink.style.display = "none";
  }

  resultsSection.style.display = "block";
}

// Utility functions
function resetDependentFields(fields) {
  fields.forEach((field) => {
    field.innerHTML = '<option value="">Select previous field first</option>';
    field.disabled = true;
  });
}

function showLoading(message) {
  const loadingModal = new bootstrap.Modal(
    document.getElementById("loadingModal")
  );
  const modalBody = document.querySelector("#loadingModal .modal-body p");
  if (modalBody && message) {
    modalBody.textContent = message;
  }
  loadingModal.show();
}

function hideLoading() {
  const loadingModal = bootstrap.Modal.getInstance(
    document.getElementById("loadingModal")
  );
  if (loadingModal) {
    loadingModal.hide();
  }
}

function showProgressSection() {
  document.getElementById("progressSection").style.display = "block";
  document.getElementById("resultsSection").style.display = "none";
}

function hideProgressSection() {
  document.getElementById("progressSection").style.display = "none";
}

function updateProgress(percentage, message) {
  document.getElementById("progressBar").style.width = percentage + "%";
  document.getElementById("progressMessage").textContent = message;
}

function showAlert(message, type) {
  const alertDiv = document.createElement("div");
  alertDiv.className = `alert alert-${type} alert-dismissible fade show mt-3`;
  alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

  document
    .querySelector(".card-body")
    .insertBefore(alertDiv, document.querySelector("#causelistForm"));

  setTimeout(() => {
    if (alertDiv.parentNode) {
      alertDiv.remove();
    }
  }, 5000);
}

function isValidDate(dateString) {
  const regex = /^(\d{2})-(\d{2})-(\d{4})$/;
  if (!regex.test(dateString)) return false;

  const parts = dateString.split("-");
  const day = parseInt(parts[0], 10);
  const month = parseInt(parts[1], 10);
  const year = parseInt(parts[2], 10);

  if (year < 2000 || year > 2030 || month === 0 || month > 12) return false;

  const monthLength = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  if (year % 400 === 0 || (year % 100 !== 0 && year % 4 === 0)) {
    monthLength[1] = 29;
  }

  return day > 0 && day <= monthLength[month - 1];
}
