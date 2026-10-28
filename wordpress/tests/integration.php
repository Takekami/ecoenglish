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
wp_update_post(array('ID' => $business, 'post_status' => 'draft'));
eel_check(!in_array($business, wp_list_pluck(Econenglish_Learning::lesson_query()->posts, 'ID')), 'drafts not exposed');
WP_CLI::success('WordPress learning navigation integration passed');
