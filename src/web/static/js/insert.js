import { displayToast } from './alert.js';

document.addEventListener("DOMContentLoaded", function() {
  const insertForm = document.getElementById('insertForm');
  const tenantNameInput = document.getElementById('tenantName');
  const tenantAddressInput = document.getElementById('tenantAddress');
  const csvFileInput = document.getElementById('csvFile');
  const progressBar = document.getElementById('progressBar');
  const progressBarStatus = document.getElementById('progressBarStatus');
  const insertButton = document.getElementById('insertBtn');

  insertButton.addEventListener('click', handleInsertClick);

  function handleInsertClick() {
    const tenantName = tenantNameInput.value;
    const tenantAddress = tenantAddressInput.value;
    const file = csvFileInput.files[0];

    if (tenantName && tenantAddress) {
      submitTenantInfo(tenantName, tenantAddress);
    }

    if (file) {
      uploadFile(file);
    }
    csvFileInput.value = '';
  }

  function submitTenantInfo(tenantName, tenantAddress) {
    const data = { name: tenantName, address: tenantAddress };
    const url = '/insert/_tenant';
    makeRequest(url, 'POST', JSON.stringify(data), handleTenantResponse);
  }

  function handleTenantResponse(response, status) {
    if (status === 201) {
      displayToast("Tenant information added.", "#5cb85c");
    } else {
      displayToast(`Error - ${response.statusText}`, "#dc3545");
    }
    tenantNameInput.value = '';
    tenantAddressInput.value = '';
  }

  function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/insert/_batch', true);

    xhr.upload.onprogress = updateProgressBar;
    xhr.onload = () => handleFileUploadResponse(xhr);

    xhr.send(formData);
  }

  function updateProgressBar(e) {
    if (e.lengthComputable) {
      const percentComplete = (e.loaded / e.total) * 100;
      progressBar.style.display = 'block';
      progressBarStatus.style.width = percentComplete + '%';
    }
  }

  function handleFileUploadResponse(xhr) {
    const response = JSON.parse(xhr.responseText);
    const total = response.success + response.failed;
    const successMessage = `Imported ${response.success}/${total} entries.`;
    if (xhr.status === 201) {
      displayToast(successMessage, "#5cb85c");
    } else if (xhr.status === 206) {
      displayToast(successMessage, "#ffc107");
    } else {
      displayToast("Error - File upload failed.", "#dc3545");
    }
    progressBar.style.display = 'none';
    progressBarStatus.style.width = '0%';
  }


  function makeRequest(url, method, data, callback) {
    const xhr = new XMLHttpRequest();
    xhr.open(method, url, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function() {
      callback(xhr.response, xhr.status);
    };
    xhr.onerror = function() {
      displayToast("Error - Could not send request.", "#dc3545");
    };
    xhr.send(data);
  }
});
