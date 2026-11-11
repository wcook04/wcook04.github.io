/* Runs before first paint: marks the page as scripted so the stage can show one
   project at a time without a flash of all of them. */
document.documentElement.className += ' js';
