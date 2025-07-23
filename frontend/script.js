document.addEventListener("DOMContentLoaded", () => {
  AOS.init(); // Initialize AOS library for scroll animations

  // Dropdown management
  const dropdowns = {
    objectives: false,
    members: false,
    highlights: false,
    about: false,
  };

  window.toggleDropdown = function (menu) {
    for (let key in dropdowns) {
      const dropdownElement = document.getElementById(`dropdown-${key}`);
      const dropdownMenu = document.getElementById(`${key}-menu`);

      if (key !== menu) {
        if (dropdownElement) {
          dropdownElement.classList.add("hidden");
        }
        if (dropdownMenu) {
          dropdownMenu.classList.remove("active");
        }
        dropdowns[key] = false;
      }
    }

    const dropdown = document.getElementById(`dropdown-${menu}`);
    const menuContainer = document.getElementById(`${menu}-menu`);

    if (dropdown) {
      dropdown.classList.toggle("hidden");
    }
    if (menuContainer) {
      menuContainer.classList.toggle("active");
    }
    dropdowns[menu] = !dropdowns[menu];
  };

  // Hide dropdowns when clicking outside
  document.addEventListener("click", function (event) {
    const headerNav = document.querySelector(".nav");
    if (headerNav && !headerNav.contains(event.target)) {
      document.querySelectorAll(".dropdown-content").forEach((el) => {
        el.classList.add("hidden");
      });
      document.querySelectorAll(".dropdown").forEach((el) => {
        el.classList.remove("active");
      });
      for (let key in dropdowns) {
        dropdowns[key] = false;
      }
    }
  });

  // Highlight slideshow logic
  const slideshowImages = [
    "highlight1.jpg",
    "highlight2.jpg",
    "highlight3.jpg",
  ]; // Add your image paths here
  let currentSlide = 0;

  function showSlide(idx) {
    const img = document.getElementById("slideshow-img");
    if (img) {
      img.src = slideshowImages[idx];
    }
  }

  window.prevSlide = function () {
    currentSlide =
      (currentSlide - 1 + slideshowImages.length) % slideshowImages.length;
    showSlide(currentSlide);
  };

  window.nextSlide = function () {
    currentSlide = (currentSlide + 1) % slideshowImages.length;
    showSlide(currentSlide);
  };

  // Auto slideshow - only runs if the picture tab is active
  setInterval(() => {
    const highlightPicSection = document.getElementById("highlight-pic");
    if (highlightPicSection && !highlightPicSection.classList.contains("hidden")) {
      nextSlide();
    }
  }, 3000); // Change image every 3 seconds

  // Tab logic for highlights (Pictures/Videos)
  window.showHighlightTab = function (tab) {
    const picTabContent = document.getElementById("highlight-pic");
    const vidTabContent = document.getElementById("highlight-vid");
    const picTabButton = document.getElementById("picTab");
    const vidTabButton = document.getElementById("vidTab");
    const highlightVideo = document.getElementById("highlight-video");

    if (picTabContent && vidTabContent && picTabButton && vidTabButton) {
      if (tab === "pic") {
        picTabContent.classList.remove("hidden");
        vidTabContent.classList.add("hidden");
        picTabButton.classList.add("active");
        vidTabButton.classList.remove("active");
        if (highlightVideo) {
          highlightVideo.pause(); // Pause video when switching to pictures
        }
      } else if (tab === "vid") {
        picTabContent.classList.add("hidden");
        vidTabContent.classList.remove("hidden");
        picTabButton.classList.remove("active");
        vidTabButton.classList.add("active");
        if (highlightVideo) {
          highlightVideo.play(); // Autoplay video when switching to video tab
        }
      }
    }
  };

  // Default to pictures tab on load
  showHighlightTab("pic");

  // Video mute/unmute logic
  window.toggleMute = function () {
    const video = document.getElementById("highlight-video");
    if (video) {
      video.muted = !video.muted;
    }
  };
});