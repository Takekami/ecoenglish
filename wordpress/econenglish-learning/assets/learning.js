(function () {
  'use strict';
  const config = window.eelConfig || {};
  const lesson = document.querySelector('[data-eel-page="lesson"]');
  const guide = document.querySelector('[data-eel-page="guide"]');
  const library = document.querySelector('[data-eel-page="library"]');
  const root = lesson || guide || library || document.querySelector('.eel-home');
  const seen = new Set();

  // Use Site Kit's existing tag and consent settings; never insert another tracker.
  function send(name, params) {
    if (config.admin || !root || typeof window.gtag !== 'function') return;
    window.gtag('event', name, Object.assign({
      send_to: config.measurementId,
      lesson_id: lesson ? lesson.dataset.eelLesson : '0',
      learning_page: root.dataset.eelPage || 'home',
      transport_type: 'beacon'
    }, params || {}));
  }

  document.addEventListener('click', function (event) {
    const link = event.target.closest('a[data-eel-event]');
    if (!link) return;
    send(link.dataset.eelEvent, {
      target_lesson_id: link.dataset.eelTarget || '0',
      lesson_topic: link.dataset.eelTopic || 'all'
    });
  });

  if (lesson) {
    const article = lesson.closest('article') || lesson.parentElement;
    article.querySelectorAll('audio').forEach(function (audio, index) {
      audio.addEventListener('play', function () {
        const key = 'play:' + index;
        if (!seen.has(key)) { seen.add(key); send('lesson_audio_start', {player_type: 'html_audio'}); }
      });
      audio.addEventListener('ended', function () {
        const key = 'end:' + index;
        if (!seen.has(key)) { seen.add(key); send('lesson_audio_complete', {player_type: 'html_audio'}); }
      });
    });
    article.querySelectorAll('details').forEach(function (detail, index) {
      const summary = detail.querySelector('summary');
      if (!summary || !/Answers|解答|答え/i.test(summary.textContent)) return;
      detail.addEventListener('toggle', function () {
        if (!detail.open || seen.has('answer:' + index)) return;
        seen.add('answer:' + index);
        send('lesson_answer_open', {question_group: /Listening|リスニング/i.test(summary.textContent) ? 'listening' : /Reading|リーディング/i.test(summary.textContent) ? 'reading' : 'other'});
      });
    });
    // Cross-origin Spreaker iframe playback is not observable: do not count focus as play.
  }

  // Footer markup is moved into the main content so the guide is visible before posts.
  const entry = document.querySelector('.eel-home');
  const main = document.querySelector('#main-contents, main');
  if (entry && main) main.prepend(entry);
}());
