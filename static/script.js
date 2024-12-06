



function deleteRow(rowElement) {
    console.log("Delete Row function triggered."); // Debugging Step 1
    const confirmation = confirm("Are you sure you want to delete this row?");
    if (!confirmation) {
        console.log("Row deletion canceled by user."); // Debugging Step 2
        return;
    }

    // Get table and row details
    const tableName = rowElement.closest("table").getAttribute("data-table-name");
    const rowId = rowElement.getAttribute("data-row-id");

    console.log(`Table Name: ${tableName}, Row ID: ${rowId}`); // Debugging Step 3

    // Send DELETE request to server
    fetch('/delete_row/' + tableName + '/' + rowId, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        console.log("Response received from server."); // Debugging Step 4
        return response.json();
    })
    .then(data => {
        console.log("Server response data:", data); // Debugging Step 5
        if (data.success) {
            alert("Row deleted successfully!");
            rowElement.remove(); // Remove the row from the page
        } else {
            alert("Error deleting row: " + data.error);
        }
    })
    .catch(error => {
        console.error("Error occurred while deleting the row:", error); // Debugging Step 6
        alert("An error occurred while deleting the row.");
    });
}




function editRow(row) {
    const tableName = row.closest('table').dataset.tableName;
    const rowId = row.dataset.rowId;
    window.location.href = `/edit/${tableName}/${rowId}`;

    // Add logic to open a modal or navigate to the edit page.
}


function logout() {
    // Clear session or token (this depends on how authentication is managed, this is just an example)
    localStorage.removeItem('userAuthToken'); // Assuming JWT or other token is stored in local storage
    
    // Redirect to login page
    window.location.href = '/login';  // Change the path to your login page
}