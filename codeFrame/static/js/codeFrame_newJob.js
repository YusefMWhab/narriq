// Global Variable

let dataFile = null;
let method = null;

let userMapping = null;
let projectDescription = null;
let projectFieldRegion = null;
let projectResultLanguage = null;


document.addEventListener('DOMContentLoaded', () => {

    // 1. Upload Data Section Logic
    const fileRadio = document.getElementById("upload-file");
    const textRadio = document.getElementById("paste-text");

    const fileInput = document.getElementById("file-input");
    const fileNameDisplay = document.getElementById("file-name");

    fileRadio.addEventListener("change", uploadData_toggleSections);
    textRadio.addEventListener("change", uploadData_toggleSections);

    fileInput.addEventListener("change", function () {
        const fileName = this.files[0]?.name;
        fileNameDisplay.innerText = fileName ? "Selected file: " + fileName : "";
    });

    // Buttons actions & Event Listeners
    const uploadData_submitBtn = document.getElementById("uploadData-submitBtn");
    const uploadData_cancelBtn = document.getElementById("uploadData-cancelBtn");

    uploadData_submitBtn.addEventListener("click", uploadData_submit);
    uploadData_cancelBtn.addEventListener("click", () => {
        // Reset form fields
        document.getElementById("file-input").value = "";
        fileNameDisplay.innerText = "";
        document.getElementById("data-text-input").value = "";

    });

    // 2. Map Columns Section Logic



    // 3. Column Description Section Logic

});

/* ==================== Functions ==================== */

// Function to toggle between file upload and text input sections
function uploadData_toggleSections() {
    const fileSection = document.getElementById("file-upload-section");
    const textSection = document.getElementById("text-upload-section");
    const fileRadio = document.getElementById("upload-file");
    const fileInput = document.getElementById("file-input");
    const fileNameDisplay = document.getElementById("file-name");

    if (fileRadio.checked) {
        fileSection.style.display = "block";
        textSection.style.display = "none";
        document.getElementById("data-text-input").value = "";
    } else {
        document.getElementById("file-input").value = "";
        document.getElementById("file-name").innerText = "";
        fileSection.style.display = "none";
        textSection.style.display = "block";
    }
}

// Upload Data Submit Button
function uploadData_submit() {

    // Clear previous variables
    dataFile = null;
    method = null;
    userMapping = null;
    projectDescription = null;
    projectFieldRegion = null;
    projectResultLanguage = null;

    // Check Radio Buttons
    const selectedMethod = document.querySelector(
        'input[name="upload-method"]:checked'
    ).value;

    // Read User input
    if (selectedMethod === "file") {
        dataFile = read_File_Data();
        method = "file";

    } else if (selectedMethod === "text") {
        dataFile = read_TextArea_Data();
        method = "text";
    }

    if (!dataFile) {
        return;
    }

    handleMapping();
}

// Function to read data from the text area and convert it to a format suitable for backend processing
function read_TextArea_Data() {

    const text = document.getElementById("data-text-input").value.trim();

    if (!text) {
        showAlert("Please enter some text", "warning");
        return null;
    }

    const blob = new Blob([text], { type: "text/csv" });

    // Return the FormData File to the backend for processing
    return blob;
}

// Function to read the uploaded file and convert it to a format suitable for backend processing
function read_File_Data() {

    const fileInput = document.getElementById("file-input");

    if (!fileInput.files.length) {
        showAlert("Please upload a file first", "warning");
        return null;
    }
    const file = fileInput.files[0];

    // Return the FormData File to the backend for processing
    return file;
}

// Function to handle the column mapping logic and prepare the data for the next step
async function handleMapping() {
    // Clear previous variables
    userMapping = null;
    projectDescription = null;

    const numberInputField = document.getElementById("num-columns-field");
    const numberInput = document.getElementById("num-columns-input");
    const headersFields = document.getElementById("headers-fields");

    // Display the mapping card and hide the upload card
    document.getElementById("mapping-card").style.display = "flex";
    document.getElementById("upload-data-card").style.display = "none";

    let headers = [];

    if (method === "file") {

        const reader = new FileReader();
        reader.onload = function (event) {
            try {
                const data = new Uint8Array(event.target.result);
                const workbook = XLSX.read(data, { type: 'array' });
                const firstSheetName = workbook.SheetNames[0];
                const worksheet = workbook.Sheets[firstSheetName];

                rawData = XLSX.utils.sheet_to_json(worksheet, {
                    header: 1,
                    defval: ""
                });

                if (rawData.length > 0) {
                    headers = rawData[0];
                }
            } catch (error) {
                console.error("Error parsing Excel:", error);
                showAlert("Error parsing Excel file. Please ensure it's a valid .xlsx file.", "warning");
            }
        };

        const file = document.getElementById("file-input").files[0];
        if (file) {
            reader.readAsArrayBuffer(file);
        } else {
            showAlert("Please select a file first.", "warning");
        }

        // Show the column number input field
        numberInputField.style.display = "flex";

        // listen for number change
        numberInput.addEventListener("input", () => {

            const count = parseInt(numberInput.value);

            if (!count || count <= 0) return;
            if (headers.length === 0) return;

            File_renderMapping(headersFields, headers, count);
        });

    }

    else if (method === "text") {
        headers = ["text"];
        Text_renderMapping(headersFields);
    }


    // Buttons actions & Event Listeners
    const mapColumns_submitBtn = document.getElementById("mapColumns-submitBtn");
    const mapColumns_cancelBtn = document.getElementById("mapColumns-cancelBtn");

    // uploadData_submitBtn.addEventListener("click", );
    mapColumns_submitBtn.addEventListener("click", startProcess);
    mapColumns_cancelBtn.addEventListener("click", () => {

        // Reset UI 

        document.getElementById("job-regionField-input").value = "";
        document.getElementById("job-outputLanguage-input").value = "";

        document.getElementById("job-desc-input").value = "";

        document.getElementById("num-columns-input").value = "";
        document.getElementById("num-columns-field").style.display = "none";

        document.getElementById("headers-fields").innerHTML = "";

        document.getElementById("mapping-card").style.display = "none";
        document.getElementById("upload-data-card").style.display = "flex";

        document.getElementById("file-input").value = "";
        document.getElementById("file-name").innerText = "";
        document.getElementById("data-text-input").value = "";


    });

}

function File_renderMapping(container, headers, count) {

    container.innerHTML = ""; // reset

    for (let i = 0; i < count; i++) {

        const row = document.createElement("div");
        row.className = "file-mapping-row";

        row.innerHTML = `

            <select class="column-select user-mapping-select">
                placeholder="Enter the category for the job...">
                <option value="">Select a category</option>
                ${headers.map(h => `<option value="${h}">${h}</option>`).join("")}
            </select>

            <textarea class="user-mapping-textarea" placeholder="Describe this column"></textarea>
        `;

        container.appendChild(row);
    }
}

function Text_renderMapping(container) {

    container.innerHTML = ""; // reset

    const row = document.createElement("div");
    row.className = "text-mapping-row";

    row.innerHTML = `

            <textarea class="user-mapping-textarea" placeholder="Describe this Data"></textarea>
        `;

    container.appendChild(row);

}

async function startProcess() {


    const mapColumns_submitBtn = document.getElementById("mapColumns-submitBtn");

    const jobRegionFiled = document.getElementById("job-regionField-input").value;
    const jobResultLanguage = document.getElementById("job-outputLanguage-input").value;

    const jobDescription = document.getElementById("job-desc-input").value.trim();

    const mappingData = [];

    // Validation
    if (!jobRegionFiled || !jobDescription || !jobResultLanguage) {
        showAlert("Please fill field region, Select result language, and project description", "warning");
        return;
    }


    // لو File Mapping
    if (method === "file") {

        const colNumber = document.getElementById("num-columns-input").value
        if (!colNumber || colNumber === 0) {
            showAlert("Please Enter number of the requred columns", "warning");
            return;
        }

        const mappingRows = document.querySelectorAll(".file-mapping-row");

        for (const row of mappingRows) {

            const selectElement = row.querySelector(".column-select");
            const textareaElement = row.querySelector(".user-mapping-textarea");

            const column = selectElement.value.trim();
            const description = textareaElement.value.trim();

            // Validation
            if (!column) {
                showAlert("Please select a column", "warning");
                selectElement.focus();
                return;
            }

            if (!description) {
                showAlert("Please write description for all columns", "warning");
                textareaElement.focus();
                return;
            }

            mappingData.push({
                column,
                description
            });
        }
    }
    else if (method === "text") {

        const row = document.querySelector(".text-mapping-row");
        const description = row.querySelector(".user-mapping-textarea").value.trim();

        if (!description) {
            showAlert("Please write description for the data", "warning");
            textareaElement.focus();
            return;
        }

        mappingData.push({
            column: "text",
            description: description
        });
    }
    if (await confirmWindow("Are you sure you want to start the process?")) {

        mapColumns_submitBtn.disabled = true;
        mapColumns_submitBtn.innerText = "Processing...";

        userMapping = mappingData;
        projectFieldRegion = jobRegionFiled;
        projectResultLanguage = jobResultLanguage;
        projectDescription = jobDescription;

        // Prepare data to send to backend
        try {

            const formData = new FormData();

            // file
            formData.append("dataFile", dataFile);

            // normal data
            formData.append("method", method);

            formData.append("projectFieldRegion", projectFieldRegion);
            formData.append("projectResultLanguage", projectResultLanguage);

            formData.append("projectDescription", projectDescription);

            // array/object
            formData.append(
                "userMapping",
                JSON.stringify(userMapping)
            );

            const response = await fetch("/jobs/create/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken"),
                },
                body: formData
            });

            const data = await response.json();

            if (response.ok && data.status === "success") {
                showAlert("Job created successfully!", "success");
                setTimeout(() => {
                    window.location.reload();
                }, 4000);
            }
            else {
                mapColumns_submitBtn.disabled = false;
                mapColumns_submitBtn.innerText = "Start Process";
                const errorMsg = data.message || "An error occurred while creating the job.";
                showAlert(errorMsg, "error");
            }

        } catch (error) {
            // Handle network errors or unexpected issues
            mapColumns_submitBtn.disabled = false;
            mapColumns_submitBtn.innerText = "Start Process";
            console.error("Fetch Error:", error);
            showAlert("Network error. Please check your connection.", "error");
        }


    }
    else {
        // User cancelled the action
        return;
    }
}

function getCookie(name) {

    let cookieValue = null;

    if (document.cookie && document.cookie !== "") {

        const cookies = document.cookie.split(";");

        for (let cookie of cookies) {

            cookie = cookie.trim();

            if (cookie.startsWith(name + "=")) {

                cookieValue = decodeURIComponent(
                    cookie.substring(name.length + 1)
                );

                break;
            }
        }
    }

    return cookieValue;
}


