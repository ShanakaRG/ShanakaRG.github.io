/* Shanaka Ramesh Gunasekara — site behaviour
   1. light/dark theme toggle (remembers your choice, falls back to system)
   2. mobile navigation
   3. scroll reveal
   4. portrait fallback
*/

/* --- 1. Theme -----------------------------------------------------------
   Runs immediately (this script is in <head>) so there's no flash of the
   wrong theme on load. */
(function () {
  var stored = null;
  try { stored = localStorage.getItem('theme'); } catch (e) {}
  var prefersDark = window.matchMedia &&
    window.matchMedia('(prefers-color-scheme: dark)').matches;
  var theme = stored || (prefersDark ? 'dark' : 'light');
  document.documentElement.setAttribute('data-theme', theme);
})();

document.addEventListener('DOMContentLoaded', function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* toggle button */
  var toggle = document.querySelector('.theme-toggle');
  if (toggle) {
    var sync = function () {
      var t = document.documentElement.getAttribute('data-theme');
      toggle.setAttribute('aria-label',
        t === 'dark' ? 'Switch to light theme' : 'Switch to dark theme');
    };
    sync();
    toggle.addEventListener('click', function () {
      var current = document.documentElement.getAttribute('data-theme');
      var next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      try { localStorage.setItem('theme', next); } catch (e) {}
      sync();
    });
  }

  /* --- 2. Mobile navigation --------------------------------------------- */
  var navToggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('site-nav');
  if (navToggle && nav) {
    navToggle.addEventListener('click', function () {
      var open = nav.classList.toggle('is-open');
      navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    nav.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') {
        nav.classList.remove('is-open');
        navToggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  /* --- 3. Scroll reveal -------------------------------------------------- */
  var revealables = document.querySelectorAll('.reveal');
  if (revealables.length) {
    if (reduceMotion || !('IntersectionObserver' in window)) {
      revealables.forEach(function (el) { el.classList.add('is-visible'); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            io.unobserve(entry.target);
          }
        });
      }, { rootMargin: '0px 0px -6% 0px', threshold: 0.04 });
      revealables.forEach(function (el) { io.observe(el); });
    }
  }

  /* --- 4. Portrait fallback --------------------------------------------- */
  var portrait = document.querySelector('.portrait');
  if (portrait) {
    portrait.addEventListener('error', function () {
      var box = document.createElement('div');
      box.className = 'portrait-fallback';
      box.textContent = (portrait.getAttribute('data-initials') || 'SG');
      box.setAttribute('aria-label', 'Portrait placeholder');
      portrait.replaceWith(box);
    });
  }
});
