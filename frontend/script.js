async function uploadFile() {
    const fileInput = document.getElementById("fileInput");
    const file = fileInput.files[0];
    if (!file) {
        alert("Please select a file to upload!");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch("http://localhost:8000/upload/", {
            method: "POST",
            body: formData,
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log("Received data from /upload/:", data);
        displayFlashcards(data);
    } catch (error) {
        console.error("Error uploading file:", error);
        alert("Failed to upload file: " + error.message);
    }
}

async function processText() {
    const textInput = document.getElementById("textInput");
    const text = textInput.value.trim();

    if (!text) {
        alert("Please enter some text!");
        return;
    }

    console.log("Submitting text:", text.substring(0, 50) + "...");
    try {
        const response = await fetch("http://localhost:8000/text/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ text: text }),
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log("Received raw data from /text/:", data);
        if (!Array.isArray(data)) {
            console.error("Invalid response format, expected an array:", data);
            alert("Invalid response from server. Check console for details.");
            return;
        }
        console.log("Processed data for display:", data);
        displayFlashcards(data);
    } catch (error) {
        console.error("Error processing text:", error);
        alert("Failed to process text: " + error.message);
    }
}

function displayFlashcards(flashcards) {
    console.log("Attempting to display flashcards:", flashcards);
    const container = document.getElementById("flashcard-container");
    if (!container) {
        console.error("Flashcard container not found in DOM! Check if 'flashcard-container' div exists in index.html.");
        alert("Error: Flashcard container not found in DOM.");
        return;
    }

    // Clear previous flashcards
    container.innerHTML = "";
    console.log("Cleared previous content in flashcard-container");

    if (!flashcards || flashcards.length === 0) {
        container.innerHTML = "<p>No flashcards generated. Try different text or check the backend logs.</p>";
        console.warn("No flashcards to display");
        return;
    }

    console.log(`Rendering ${flashcards.length} flashcards`);
    flashcards.forEach((card, index) => {
        console.log(`Processing flashcard ${index + 1}:`, card);
        // Validate card structure
        if (!card.front || !card.back || !card.category) {
            console.warn(`Skipping invalid flashcard at index ${index}:`, card);
            return;
        }

        const div = document.createElement("div");
        div.className = "flashcard";
        div.innerHTML = `
            <strong>Question: ${card.front}</strong>
            <p style="display:none;">Answer: ${card.back}</p>
            <small>Category: ${card.category}</small>
        `;
        div.onclick = () => {
            const p = div.querySelector("p");
            p.style.display = p.style.display === "none" ? "block" : "none";
        };
        container.appendChild(div);
        console.log(`Appended flashcard ${index + 1} to container`);
    });

    // Verify DOM update
    const renderedCards = container.querySelectorAll(".flashcard");
    console.log(`Total flashcards rendered in DOM: ${renderedCards.length}`);
    if (renderedCards.length === 0) {
        console.error("No flashcards were rendered. Check card data and DOM structure.");
        container.innerHTML = "<p>Error: No flashcards rendered. Check console for details.</p>";
    }
}