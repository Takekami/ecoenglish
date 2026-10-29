(function () {
  'use strict';
  const config = window.eelConfig || {};
  const lesson = document.querySelector('[data-eel-page="lesson"]');
  const guide = document.querySelector('[data-eel-page="guide"]');
  const library = document.querySelector('[data-eel-page="library"]');
  const weekly = document.querySelector('[data-eel-page="weekly"]');
  const learningGuide = document.querySelector('[data-eel-page="learning-guide"]');
  const root = lesson || guide || library || weekly || learningGuide || document.querySelector('.eel-home');
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
      lesson_topic: link.dataset.eelTopic || 'all',
      study_step: ['audio', 'script', 'expression', 'listening'].includes(link.dataset.eelStep) ? link.dataset.eelStep : 'other'
    });
  });

  document.addEventListener('eel:learning', function (event) {
    const data = event.detail || {};
    if (data.name === 'lesson_mode_change' && ['full', 'listening'].includes(data.mode)) send(data.name, {study_mode: data.mode});
    if (data.name === 'lesson_mark_complete' && ['marked', 'cleared'].includes(data.action)) send(data.name, {completion_action: data.action});
    if (data.name === 'expression_repeat_toggle' && ['enabled', 'disabled'].includes(data.action)) send(data.name, {repeat_action: data.action});
  });

  if (weekly) weekly.querySelectorAll('[data-eel-weekly-answer]').forEach(function (detail, index) {
    detail.addEventListener('toggle', function () {
      if (!detail.open || seen.has('weekly:' + index)) return;
      seen.add('weekly:' + index);
      send('weekly_answer_open', {question_group: 'true_false'});
    });
  });

  if (lesson) {
    const article = lesson.closest('article') || lesson.parentElement;
    const started = new WeakSet();
    const finished = new WeakSet();
    // Media events do not bubble. Capture also covers players inserted/replaced later.
    document.addEventListener('play', function (event) {
      const audio = event.target;
      if (!audio || audio.tagName !== 'AUDIO' || !article.contains(audio) || started.has(audio)) return;
      started.add(audio);
      send(audio.dataset && audio.dataset.eelExpressionAudio === 'sentence' ? 'expression_audio_start' : 'lesson_audio_start', {player_type: 'html_audio'});
    }, true);
    document.addEventListener('ended', function (event) {
      const audio = event.target;
      if (!audio || audio.tagName !== 'AUDIO' || !article.contains(audio) || finished.has(audio)) return;
      finished.add(audio);
      send(audio.dataset && audio.dataset.eelExpressionAudio === 'sentence' ? 'expression_audio_complete' : 'lesson_audio_complete', {player_type: 'html_audio'});
    }, true);
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
