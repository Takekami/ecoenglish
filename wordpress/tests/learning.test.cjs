const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('wordpress/econenglish-learning/assets/learning.js', 'utf8');

function fixture({admin = false, tag = true, iframeOnly = false} = {}) {
  const calls = [];
  const handlers = {};
  const audioEvents = {};
  const details = [];
  const audio = {addEventListener: (name, fn) => { audioEvents[name] = fn; }};
  const article = {querySelectorAll: selector => selector === 'audio' ? (iframeOnly ? [] : [audio]) : details};
  const lesson = {dataset: {eelPage: 'lesson', eelLesson: '42'}, closest: () => article};
  const document = {
    querySelector: selector => selector === '[data-eel-page="lesson"]' ? lesson : null,
    addEventListener: (name, fn) => { handlers[name] = fn; }
  };
  const window = {eelConfig: {admin, measurementId: 'G-TEST'}};
  if (tag) window.gtag = (...args) => calls.push(args);
  function detail(label) {
    const result = {open: false, listener: null, querySelector: () => ({textContent: label}), addEventListener: (_, fn) => { result.listener = fn; }};
    details.push(result);
    return result;
  }
  const answer = detail('Listening Answersを見る');
  const vocab = detail('日本語の意味を見る');
  vm.runInNewContext(source, {window, document, Set});
  return {calls, handlers, audioEvents, answer, vocab};
}
test('play and completion counted once per player per page', () => {
  const f = fixture();
  f.audioEvents.play(); f.audioEvents.play(); f.audioEvents.ended(); f.audioEvents.ended();
  assert.deepEqual(f.calls.map(c => c[1]), ['lesson_audio_start', 'lesson_audio_complete']);
  assert.equal(f.calls[0][2].lesson_id, '42');
  assert.equal(f.calls[0][2].send_to, 'G-TEST');
});
test('only opened answers count, once, not vocabulary reveals', () => {
  const f = fixture();
  f.answer.listener(); f.answer.open = true; f.answer.listener(); f.answer.listener();
  assert.equal(f.calls.length, 1); assert.equal(f.calls[0][2].question_group, 'listening');
  assert.equal(f.vocab.listener, null);
});
test('admin and unavailable tag do not emit or install a tracker', () => {
  for (const options of [{admin: true}, {tag: false}]) {
    const f = fixture(options); f.audioEvents.play();
    assert.equal(f.calls.length, 0);
  }
});
test('related link sends IDs, no user text or destination URLs', () => {
  const f = fixture();
  f.handlers.click({target: {closest: () => ({dataset: {eelEvent: 'related_lesson_click', eelTarget: '71'}})}});
  assert.equal(f.calls[0][1], 'related_lesson_click');
  assert.equal(f.calls[0][2].target_lesson_id, '71');
  assert.equal('link_url' in f.calls[0][2], false);
});
test('iframe does not fabricate playback events', () => {
  const f = fixture({iframeOnly: true});
  assert.deepEqual(Object.keys(f.audioEvents), []);
  assert.equal(f.calls.length, 0);
});
