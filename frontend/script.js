// Typing animation for login greeting
const typeWriterText = "Welcome to InsightHub";
let i = 0;

function typeWriter() {
  if (i < typeWriterText.length) {
    document.getElementById("greet").innerHTML += typeWriterText.charAt(i);
    i++;
    setTimeout(typeWriter, 100);
  }
}

window.onload = function () {
  if (document.getElementById("greet")) {
    typeWriter();
  }

  // Optional: background animation using particles.js (if used)
  if (window.particlesJS) {
    particlesJS.load('background-animation', 'particles.json', function() {
      console.log('🎉 particles.js config loaded');
    });
  }
};
