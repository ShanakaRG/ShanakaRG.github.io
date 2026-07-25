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

  /* --- 5. Skeleton pose sequence ---------------------------------------- */
  /* A stick-figure who cheerfully welcomes visitors: both arms raised, the
     right hand waving hello, with a happy little bounce. Uses theme variables
     so it follows light/dark. */
  var svg = document.getElementById('pose-figure');
  if (svg) {
    var NS = 'http://www.w3.org/2000/svg';
    // joints: 0 head, 1 neck, 2 Rshoulder, 3 Relbow, 4 Rwrist, 5 Lshoulder,
    // 6 Lelbow, 7 Lwrist, 8 pelvis, 9 Rhip, 10 Rknee, 11 Rankle,
    // 12 Lhip, 13 Lknee, 14 Lankle
    var EDGES = [
      [0,1],[1,2],[2,3],[3,4],[1,5],[5,6],[6,7],
      [1,8],[8,9],[9,10],[10,11],[8,12],[12,13],[13,14]
    ];

    // Base pose with BOTH arms raised up in a cheer. The right forearm (3->4)
    // waves; the left arm (5,6,7) is held up high and steady. The whole figure
    // bobs a little. Legs stay planted.
    var BASE = [
      [200,84],   // 0 head
      [200,142],  // 1 neck
      [232,150],  // 2 right shoulder
      [252,116],  // 3 right elbow (raised)
      [258,74],   // 4 right wrist (up — the waving hand)
      [168,150],  // 5 left shoulder
      [150,112],  // 6 left elbow (raised)
      [140,72],   // 7 left wrist (up, cheering)
      [200,260],  // 8 pelvis
      [224,266],  // 9 right hip
      [229,340],  // 10 right knee
      [233,414],  // 11 right ankle
      [176,266],  // 12 left hip
      [171,340],  // 13 left knee
      [167,414]   // 14 left ankle
    ];

    var ghostG = document.createElementNS(NS,'g'); ghostG.setAttribute('opacity','0.16');
    var liveG = document.createElementNS(NS,'g');
    svg.appendChild(ghostG); svg.appendChild(liveG);

    function build(group, ghost) {
      var lines = EDGES.map(function () {
        var l = document.createElementNS(NS,'line');
        l.setAttribute('stroke', ghost ? 'var(--text-faint)' : 'var(--accent)');
        l.setAttribute('stroke-width', ghost ? '1' : '1.9');
        l.setAttribute('stroke-linecap','round');
        group.appendChild(l); return l;
      });
      var dots = BASE.map(function (_, i) {
        var c = document.createElementNS(NS,'circle');
        c.setAttribute('r', ghost ? '1.6' : (i === 0 ? '7' : '3.1'));
        c.setAttribute('fill', ghost ? 'var(--text-faint)' : (i === 0 ? 'var(--accent)' : 'var(--bg)'));
        if (!ghost && i !== 0) { c.setAttribute('stroke','var(--accent)'); c.setAttribute('stroke-width','1.6'); }
        group.appendChild(c); return c;
      });
      // both raised hands glow as the cheerful "signal" keypoints
      if (!ghost) { [4,7].forEach(function (i) {
        dots[i].setAttribute('fill','var(--accent)'); dots[i].setAttribute('stroke','var(--accent)');
      }); }
      return { lines: lines, dots: dots };
    }
    var ghost = build(ghostG, true), live = build(liveG, false);

    function paint(t, pose) {
      EDGES.forEach(function (e, i) {
        var a = pose[e[0]], b = pose[e[1]];
        t.lines[i].setAttribute('x1',a[0]); t.lines[i].setAttribute('y1',a[1]);
        t.lines[i].setAttribute('x2',b[0]); t.lines[i].setAttribute('y2',b[1]);
      });
      pose.forEach(function (p, i) { t.dots[i].setAttribute('cx',p[0]); t.dots[i].setAttribute('cy',p[1]); });
    }

    // A cheerful welcome pose.
    //   wave  (-1..1): the right forearm swings the hand side to side
    //   bob   (-1..1): the whole body lifts a little on the upbeat
    var R_ELBOW = [252,116], R_FOREARM = 46;
    function cheerPose(wave, bob) {
      var lift = -bob * 5;                       // vertical bounce, px
      var p = BASE.map(function (pt) { return [pt[0], pt[1] + lift]; });
      // right forearm pivots at the elbow, sweeping ±30° for an energetic wave
      var ang = (-90 + wave * 30) * Math.PI / 180;
      p[4] = [R_ELBOW[0] + R_FOREARM * Math.cos(ang),
              R_ELBOW[1] + lift + R_FOREARM * Math.sin(ang)];
      // right elbow gives a little as the hand swings, so it isn't stiff
      p[3] = [R_ELBOW[0] + wave * 4, R_ELBOW[1] + lift - Math.abs(wave) * 2];
      // ankles stay on the ground (cancel the lift) so it bounces, not floats
      p[11][1] = BASE[11][1]; p[14][1] = BASE[14][1];
      return p;
    }

    // caption is set in the HTML ("Hello, Welcome to my profile"); leave it.

    if (reduceMotion) {
      ghostG.setAttribute('opacity','0');
      paint(live, cheerPose(0.5, 0));
    } else {
      paint(ghost, cheerPose(-1, -1));
      var t0 = null, PERIOD = 750;   // brisk, happy tempo (ms per wave)
      var animate = function (now) {
        if (t0 === null) t0 = now;
        var phase = (now - t0) / PERIOD * Math.PI * 2;
        var wave = Math.sin(phase);
        var bob = Math.sin(phase * 2);           // bounce twice per wave — bouncy!
        paint(live, cheerPose(wave, bob));
        requestAnimationFrame(animate);
      };
      requestAnimationFrame(animate);
    }
  }
});
