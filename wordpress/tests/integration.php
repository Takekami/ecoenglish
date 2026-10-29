<?php
// Runs only against the isolated CI WordPress database, never production.
function eel_check($condition, $message) {
    if (!$condition) { throw new RuntimeException($message); }
    WP_CLI::log('PASS ' . $message);
}
function eel_fixture($title, $script = 'Companies make products.') {
    return wp_insert_post(array('post_type' => 'post', 'post_status' => 'publish', 'post_title' => $title,
        'post_content' => '<audio controls src="https://example.org/test.mp3"></audio><h2>Script</h2><p>' . $script . '</p><h2>Vocabulary</h2><p>inflation</p>'));
}
$prices = eel_fixture('Inflation and wages rise');
$business = eel_fixture('Royal Mail acquisition');
$finance = eel_fixture('Yen falls as interest rates change');
$ordinary = wp_insert_post(array('post_title' => 'Diary inflation', 'post_content' => 'My diary', 'post_status' => 'publish'));
eel_check(get_post_meta($ordinary, '_econ_lesson', true) !== '1', 'ordinary posts excluded');
eel_check(in_array('prices', wp_get_object_terms($prices, 'econ_topic', array('fields' => 'slugs')), true), 'new lessons automatically classified');
eel_check(in_array('finance', wp_get_object_terms($finance, 'econ_topic', array('fields' => 'slugs')), true), 'finance topic assigned');
eel_check(!in_array('prices', wp_get_object_terms($business, 'econ_topic', array('fields' => 'slugs')), true), 'vocabulary boilerplate does not affect topic');
eel_check(Econenglish_Learning::classify('A chipmaker story', '<h2>Script</h2>Carbon emissions fall.<h2>Vocabulary</h2>') === array('energy'), 'script-only matching retains strongest topic');
eel_check(Econenglish_Learning::classify('A chair is moved', '') === array('society'), 'AI must match a whole word');
eel_check(Econenglish_Learning::classify('Israeli forces deploy snipers, tear gas, live fire in Nablus raid', '') === array('society'), 'tear gas is not energy');
eel_check(Econenglish_Learning::classify('Musk firms sue Apple and OpenAI', '') === array('business'), 'technology companies classified from headline');
eel_check(Econenglish_Learning::classify('Australian households living too large', '') === array('prices'), 'plural households classified as daily life');
$_GET = array('lesson_topic' => 'prices');
$html = Econenglish_Learning::library();
eel_check(strpos($html, 'Inflation and wages rise') !== false && strpos($html, 'Royal Mail acquisition') === false, 'topic filter excludes unrelated lessons');
$_GET = array('lesson_topic' => array('unexpected'), 'lesson_page' => array('bad'));
eel_check(strpos(Econenglish_Learning::library(), 'すべての教材') !== false, 'malformed query parameters safe');
$_GET = array();
for ($i = 0; $i < 13; $i++) { eel_fixture('Company acquisition ' . $i); }
$html = Econenglish_Learning::library();
eel_check(strpos($html, 'lesson_page=2') !== false, 'library paginates');
$_GET = array('lesson_page' => '2');
eel_check(strpos(Econenglish_Learning::library(), '前の教材へ') !== false, 'second page has previous link');
$_GET = array();
$guide = (int) get_option('econ_guide_id');
$library = (int) get_option('econ_library_id');
eel_check(get_post_status($guide) === 'publish' && get_post_status($library) === 'publish', 'guide and library published');
eel_check(strpos(Econenglish_Learning::guide(), '10分から') !== false, 'guide renders study steps');
$original = get_post_field('post_content', $guide);
Econenglish_Learning::activate();
eel_check((int) get_option('econ_guide_id') === $guide && (int) get_option('econ_library_id') === $library, 'activation idempotent');
eel_check(get_post_field('post_content', $guide) === $original, 'activation preserves existing content');
foreach (array('weekly', 'news-study', 'listening-help', 'inflation-words') as $kind) {
    $id = (int) get_option('econ_' . $kind . '_id');
    eel_check($id && get_post_status($id) === 'publish', $kind . ' growth page published');
}
$ids = array_map(function ($key) { return (int) get_option('econ_' . $key . '_id'); }, array('weekly', 'news-study', 'listening-help', 'inflation-words'));
Econenglish_Growth::setup();
eel_check($ids === array_map(function ($key) { return (int) get_option('econ_' . $key . '_id'); }, array('weekly', 'news-study', 'listening-help', 'inflation-words')), 'growth setup does not duplicate pages');
$wrapped = Econenglish_Growth::study_content('<html><head><link href="bootstrap.css"></head><body><h2>Audio</h2><audio></audio><h2>Script</h2><p>Unchanged script.</p><h2>Listening Questions</h2><ol><li>Question</li></ol></body></html>');
eel_check(strpos($wrapped, 'id="eel-script"') !== false && strpos($wrapped, 'Unchanged script.') !== false, 'study sections retain original content');
eel_check(strpos($wrapped, '<html>') === false && strpos($wrapped, 'bootstrap.css') === false, 'legacy document wrappers removed at render time');
$quiz_html = '<h2>Listening Questions</h2><ol><li>True/False: A company can invest.</li><li>Other question.</li></ol><details><summary>Listening Answers</summary><ol><li>True</li><li>b)</li></ol></details><h2>Reading Questions</h2>';
eel_check(Econenglish_Growth::quiz($quiz_html) === array('question' => 'True/False: A company can invest.', 'answer' => 'True'), 'weekly copies question and answer exactly');
eel_check(Econenglish_Growth::quiz(str_replace('<li>True</li>', '<li>b)</li>', $quiz_html)) === null, 'weekly skips malformed answer instead of guessing');
list($week_start, $week_end) = Econenglish_Growth::week_bounds(new DateTimeImmutable('2026-10-26 00:01:00', new DateTimeZone('Australia/Brisbane')));
eel_check($week_start->format('Y-m-d') === '2026-10-19' && $week_end->format('Y-m-d') === '2026-10-26', 'weekly rolls over on local Monday');
list($start, $end) = Econenglish_Growth::week_bounds();
$last_week = eel_fixture('Last week company news');
wp_update_post(array('ID' => $last_week, 'post_date' => $start->modify('+1 day')->format('Y-m-d H:i:s'), 'post_content' => '<audio></audio><h2>Script</h2><p>A company can invest.</p>' . $quiz_html));
$weekly = Econenglish_Growth::weekly();
eel_check(strpos($weekly, 'Last week company news') !== false && strpos($weekly, 'True/False: A company can invest.') !== false, 'weekly renders eligible previous-week lesson');
wp_update_post(array('ID' => $last_week, 'post_status' => 'draft'));
eel_check(strpos(Econenglish_Growth::weekly(), 'Last week company news') === false, 'weekly excludes unpublished lessons');
eel_check(wp_next_scheduled('econ_weekly_refresh') !== false, 'weekly cache refresh scheduled');
eel_check(strpos(Econenglish_Growth::article(array('key' => 'inflation-words')), 'purchasing power') !== false, 'editorial vocabulary guide renders');
global $wp_query, $wp_the_query;
$wp_query = new WP_Query(array('p' => $prices));
$wp_the_query = $wp_query;
$wp_query->the_post();
$rendered = apply_filters('the_content', get_the_content());
eel_check(strpos($rendered, 'data-eel-page="lesson"') !== false, 'lesson includes study navigation');
eel_check(strpos($rendered, 'related_lesson_click') !== false, 'lesson includes next lesson links');
$wp_query = new WP_Query(array('page_id' => $guide));
$wp_the_query = $wp_query;
$wp_query->the_post();
eel_check(strpos(apply_filters('the_content', get_the_content()), 'START HERE') !== false, 'guide renders in main WordPress loop');
wp_reset_postdata();
wp_update_post(array('ID' => $business, 'post_status' => 'draft'));
eel_check(!in_array($business, wp_list_pluck(Econenglish_Learning::lesson_query()->posts, 'ID')), 'drafts not exposed');
WP_CLI::success('WordPress learning navigation integration passed');
