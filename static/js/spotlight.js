document.addEventListener("DOMContentLoaded", () => {
  const revealLayer = document.getElementById('revealLayer');
  if (!revealLayer) return;

  // Start in the middle of the screen so you see it instantly
  let mouseX = window.innerWidth / 2;
  let mouseY = window.innerHeight / 2;
  let smoothX = mouseX;
  let smoothY = mouseY;

  window.addEventListener('mousemove', (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;
  });

  function loop() {
    // Smooth lerp (easing) for that premium trailing effect
    smoothX += (mouseX - smoothX) * 0.1;
    smoothY += (mouseY - smoothY) * 0.1;
    
    // Pass coordinates to CSS
    revealLayer.style.setProperty('--x', smoothX + 'px');
    revealLayer.style.setProperty('--y', smoothY + 'px');
    
    requestAnimationFrame(loop);
  }
  
  loop();
});
