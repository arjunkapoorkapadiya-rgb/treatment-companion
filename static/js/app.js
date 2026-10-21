document.addEventListener("DOMContentLoaded", function () {
  const flashes = document.querySelectorAll(".flash");
  flashes.forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity 0.5s, transform 0.5s";
      el.style.opacity = "0";
      el.style.transform = "translateY(-10px)";
      setTimeout(() => el.remove(), 500);
    }, 4000);
  });

  const elementsToReveal = document.querySelectorAll(".card, .ai-cta, .med-summary-card, .circle-header-card, .hero-content");
  elementsToReveal.forEach((el, index) => {
    el.classList.add("reveal");
    el.style.animationDelay = (index * 0.1) + "s";
  });

  const dateInput = document.getElementById("entry_date");
  if (dateInput && !dateInput.value) {
    dateInput.value = new Date().toISOString().split("T")[0];
  }
});
