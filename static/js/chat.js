document.addEventListener("DOMContentLoaded", function () {
  const chatForm = document.getElementById("chatForm");
  const chatInput = document.getElementById("chatInput");
  const chatBox = document.getElementById("chatBox");
  if (!chatForm) return;

  // Enable GitHub Flavored Markdown (Tables, Lists)
  marked.setOptions({
    gfm: true,
    breaks: true
  });

  let history = [];
  chatForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    const message = chatInput.value.trim();
    if (!message) return;
    
    appendMessage("user", message);
    chatInput.value = ""; 
    chatBox.scrollTop = chatBox.scrollHeight;
    
    const typingId = appendMessage("ai", "Thinking...");
    
    try {
      const response = await fetch("/api/chat", { 
        method: "POST", 
        headers: { "Content-Type": "application/json" }, 
        body: JSON.stringify({ message: message, history: history }) 
      });
      const data = await response.json();
      const typingEl = document.getElementById(typingId); 
      if (typingEl) typingEl.remove();
      
      if (data.error) { 
        appendMessage("ai", "Error: " + data.error); 
      } else {
        // Parse markdown into HTML
        appendMessage("ai", marked.parse(data.reply));
        history.push({ role: "user", content: message });
        history.push({ role: "assistant", content: data.reply });
        if (history.length > 20) history = history.slice(-20);
      }
    } catch (err) {
      const typingEl = document.getElementById(typingId); 
      if (typingEl) typingEl.remove();
      appendMessage("ai", "Connection error. Please try again.");
    }
    chatBox.scrollTop = chatBox.scrollHeight;
  });

  function appendMessage(sender, text) {
    const id = "msg-" + Date.now();
    const msgDiv = document.createElement("div"); 
    msgDiv.className = `chat-message ${sender}-message`; 
    msgDiv.id = id;
    const bubble = document.createElement("div"); 
    bubble.className = "chat-bubble";
    
    // If AI, use innerHTML for formatting. If user, use textContent.
    if (sender === "ai" && text !== "Thinking...") { 
      bubble.innerHTML = text; 
    } else { 
      bubble.textContent = text; 
    }
    
    msgDiv.appendChild(bubble); 
    chatBox.appendChild(msgDiv); 
    return id;
  }
});