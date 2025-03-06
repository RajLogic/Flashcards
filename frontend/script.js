async function uploadFile() {
    const fileInput = document.getElementById("fileInput");
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch("http://localhost:8000/upload/", {
        method: "POST",
        body: formData,
    });
    const data = await response.json();
    displayFlashcards(data.flashcards);
}

async function processText() {
    const textInput = document.getElementById("textInput");
    const text = textInput.value.trim();

    if (!text) {
        alert("Please enter some text!");
        return;
    }

    const response = await fetch("http://localhost:8000/text/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",  // Set JSON content type
        },
        body: JSON.stringify({ text: text }),  // Send JSON body
    });
    const data = await response.json();
    displayFlashcards(data.flashcards);
}

function displayFlashcards(flashcards) {
    const container = document.getElementById("flashcard-container");
    container.innerHTML = "";
    const cardMap = {}; // Map front text to div for linking

    flashcards.forEach(card => {
        const div = document.createElement("div");
        div.className = "flashcard";
        div.innerHTML = `
            <strong>Question: ${card.front}</strong>
            <p style="display:none;">Answer: ${card.back}</p>
            <small>Category: ${card.category}</small>
            ${card.links.length > 0 ? `<div>Related: ${card.links.map(link => `<span class="link" data-link="${link}">${link}</span>`).join(", ")}</div>` : ""}
        `;
        div.onclick = () => {
            const p = div.querySelector("p");
            p.style.display = p.style.display === "none" ? "block" : "none";
        };
        cardMap[card.front] = div; // Store for linking
        container.appendChild(div);
    });

    // Add click event for links
    document.querySelectorAll(".link").forEach(link => {
        link.onclick = (e) => {
            e.stopPropagation(); // Prevent flashcard toggle
            const targetFront = link.getAttribute("data-link");
            const targetDiv = cardMap[targetFront];
            if (targetDiv) {
                targetDiv.scrollIntoView({ behavior: "smooth" });
                targetDiv.querySelector("p").style.display = "block"; // Show answer
            }
        };
    });
}