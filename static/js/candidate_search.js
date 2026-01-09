// Candidate Search with AJAX
(function () {
    'use strict';

    const searchForm = document.getElementById('candidate-search-form');
    const searchInput = document.getElementById('search-input');
    const partySelect = document.getElementById('party-select');
    const resultsTable = document.getElementById('candidates-table-body');
    const loadingIndicator = document.getElementById('search-loading');
    const resultCount = document.getElementById('result-count');

    if (!searchForm || !searchInput) {
        return; // Exit if elements don't exist
    }

    let searchTimeout = null;

    // Debounced search function
    function performSearch() {
        const query = searchInput.value.trim();
        const party = partySelect ? partySelect.value : '';

        // Clear previous timeout
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }

        // Show loading indicator
        if (loadingIndicator) {
            loadingIndicator.classList.remove('d-none');
        }

        // Set new timeout (300ms debounce)
        searchTimeout = setTimeout(function () {
            // Make AJAX request
            const url = `/api/candidates/search/?q=${encodeURIComponent(query)}&party=${party}`;

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    // Hide loading indicator
                    if (loadingIndicator) {
                        loadingIndicator.classList.add('d-none');
                    }

                    // Update results count
                    if (resultCount) {
                        resultCount.textContent = data.count;
                    }

                    // Update table
                    if (resultsTable) {
                        updateTable(data.candidates);
                    }
                })
                .catch(error => {
                    console.error('Search error:', error);
                    if (loadingIndicator) {
                        loadingIndicator.classList.add('d-none');
                    }
                });
        }, 300);
    }

    // Update table with results
    function updateTable(candidates) {
        if (!resultsTable) return;

        // Clear existing rows
        resultsTable.innerHTML = '';

        if (candidates.length === 0) {
            resultsTable.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-5">
                        <i class="fas fa-search fa-3x text-muted mb-3 d-block"></i>
                        <p class="text-muted">لا توجد نتائج</p>
                    </td>
                </tr>
            `;
            return;
        }

        // Add new rows
        candidates.forEach((candidate, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${index + 1}</td>
                <td><span class="badge bg-info">${candidate.serial}</span></td>
                <td>
                    <a href="/vote/candidates/${candidate.id}/" class="text-decoration-none">
                        <strong>${candidate.full_name}</strong>
                    </a>
                </td>
                <td>${candidate.party}</td>
                <td>${candidate.voter_number}</td>
                <td>${candidate.phone}</td>
                <td><span class="badge bg-success">${candidate.total_votes.toLocaleString()}</span></td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <a href="/vote/candidates/${candidate.id}/" class="btn btn-outline-info" title="عرض">
                            <i class="fas fa-eye"></i>
                        </a>
                        <a href="/vote/candidates/${candidate.id}/edit/" class="btn btn-outline-primary" title="تعديل">
                            <i class="fas fa-edit"></i>
                        </a>
                        <a href="/vote/candidates/${candidate.id}/delete/" class="btn btn-outline-danger" title="حذف">
                            <i class="fas fa-trash"></i>
                        </a>
                    </div>
                </td>
            `;
            resultsTable.appendChild(row);
        });
    }

    // Event listeners
    if (searchInput) {
        searchInput.addEventListener('input', performSearch);
    }

    if (partySelect) {
        partySelect.addEventListener('change', performSearch);
    }

    // Prevent form submission
    if (searchForm) {
        searchForm.addEventListener('submit', function (e) {
            e.preventDefault();
            performSearch();
        });
    }
})();
