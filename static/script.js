// Function to submit prediction form via AJAX
function submitPredictionForm(fileInput) {
    const form = fileInput.closest('form');
    if (!form) return;

    const formData = new FormData(form);
    
    fetch('/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.text())
    .then(html => {
        // Replace page content with response
        document.documentElement.innerHTML = html;
        // Re-setup drop zones for new page
        setupDropZone("drop-zone", "file");
        setupDropZone("drop-zone-again", "file-again");
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Lỗi khi dự đoán: ' + error);
    });
}

// Helper function to setup drop zone
function setupDropZone(dropZoneId, fileInputId) {
    const dropZone = document.getElementById(dropZoneId);
    const fileInput = document.getElementById(fileInputId);

    if (!dropZone || !fileInput) return;

    // Click to open file explorer
    dropZone.addEventListener("click", () => {
        fileInput.click();
    });

    // Drag over event
    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.style.backgroundColor = "#e0e0e0";
        dropZone.style.borderColor = "#4CAF50";
    });

    // Drag leave event
    dropZone.addEventListener("dragleave", (e) => {
        e.stopPropagation();
        dropZone.style.backgroundColor = "#f9f9f9";
        dropZone.style.borderColor = "#ccc";
    });

    // Drop event
    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.style.backgroundColor = "#f9f9f9";
        dropZone.style.borderColor = "#ccc";

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            // Create a new DataTransfer object and add files
            const dataTransfer = new DataTransfer();
            for (let file of files) {
                dataTransfer.items.add(file);
            }
            fileInput.files = dataTransfer.files;
            
            // Trigger change event to process the file
            const changeEvent = new Event('change', { bubbles: true });
            fileInput.dispatchEvent(changeEvent);
        }
    });

    // File input change event
    fileInput.addEventListener("change", function () {
        if (this.files.length > 0) {
            const file = this.files[0];
            const reader = new FileReader();
            reader.onload = function (e) {
                dropZone.style.backgroundImage = "url(" + e.target.result + ")";
                dropZone.style.backgroundSize = "cover";
                dropZone.style.backgroundPosition = "center";
                
                // Hide text when image is loaded
                const textElement = dropZone.querySelector("p");
                if (textElement) {
                    textElement.style.display = "none";
                }
            };
            reader.readAsDataURL(file);
        }
    });
}

// Setup both drop zones on page load
document.addEventListener('DOMContentLoaded', function() {
    setupDropZone("drop-zone", "file");
    setupDropZone("drop-zone-again", "file-again");
});
