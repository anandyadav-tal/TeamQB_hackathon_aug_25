document.getElementById("uploadForm").addEventListener("submit", function(event) {
    event.preventDefault(); // Prevent the default form submission

    const formData = new FormData(this);

    fetch("/upload", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message); // Show success message
        } else {
            alert("Error: " + data.message); // Show error message
        }
    })
    .catch(error => {
        console.error("Error:", error);
        alert("An error occurred while uploading the file.");
    });
});
