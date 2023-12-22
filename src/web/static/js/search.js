// Assuming displayToast is exported from alert.js and can be imported here
import { displayToast } from './alert.js';

document.addEventListener("DOMContentLoaded", function() {
  const searchForm = document.getElementById('searchForm');
  const searchTypeSelect = document.getElementById('searchType');
  const searchInput = document.getElementById('searchInput');
  const searchBtn = document.getElementById('searchBtn');
  const downloadBtn = document.getElementById('downloadBtn');
  const searchResults = document.getElementById('searchResults');

  searchBtn.addEventListener('click', performSearch);
  downloadBtn.addEventListener('click', downloadResults);

  function performSearch() {
    const searchType = searchTypeSelect.value;
    const query = searchInput.value.trim();
    const endpoint = searchType === 'tenant' ? '/search/_addresses' : '/search/_tenants';
    const queryString = searchType === 'address' ? `?address=${encodeURIComponent(query)}` : `?name=${encodeURIComponent(query)}`;

    fetch(endpoint + queryString)
      .then(response => response.json())
      .then(data => {
        updateSearchResults(data);
        downloadBtn.disabled = data.length === 0;
      })
      .catch(error => displayToast('Error: ' + error, 'red'));
  }

  function updateSearchResults(data) {
    searchResults.innerHTML = '';
    data.forEach(item => {
      const tenantName = item.name || '';
      const address = item.address.address || '';
      const row = `<tr><td>${tenantName}</td><td>${address}</td></tr>`;
      searchResults.innerHTML += row;
    });
  }

  function downloadResults() {
    const data = Array.from(searchResults.querySelectorAll('tr'))
      .map(row => ({
        name: row.cells[0].textContent,
        address: row.cells[1].textContent
      }));

    const formattedData = formatDataForDownload(data);
    const filename = 'search_results.txt';
    initiateDownload(filename, formattedData);
  }

  function formatDataForDownload(data) {
    let tenantsByAddress = data.reduce((acc, { name, address }) => {
      acc[address] = acc[address] || [];
      acc[address].push(name);
      return acc;
    }, {});

    return Object.entries(tenantsByAddress)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([address, tenants]) => `[${address}]\n${tenants.sort().join(',')}`)
      .join('\n\n');
  }

  function initiateDownload(filename, text) {
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
    element.setAttribute('download', filename);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  }
});
