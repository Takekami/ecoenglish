<?php
if (!defined('ABSPATH')) { exit; }

/** Original editorial guides; examples below are exercises, not news claims. */
function eel_learning_articles() {
    return array(
        'news-study' => array(
            'slug' => 'study-english-with-economic-news',
            'title' => '経済ニュースで英語を勉強する方法｜無理なく続ける1週間のプラン',
            'excerpt' => '英語ニュースを教材にするときの選び方、聞く・読む・復習する順序と、1本の教材を繰り返し使う1週間の学習プランを紹介します。',
            'topic' => '',
            'html' => <<<'HTML'
<p class="eel-lead">1本を、何度か使ってみる。</p>
<p>ニュース英語の学習では、毎日違う記事を読むことだけを目標にすると、知らない単語を調べる作業で終わりがちです。まずは興味のある短い教材を1本選び、聞く・読む・自分の言葉で説明する練習に分けて使ってみましょう。</p>
<h2>最初の教材は「知っている話題」から選ぶ</h2>
<p>物価や買い物、身近な企業のニュースなど、背景を少し知っている話題を選ぶと、英語の表現そのものに注意を向けやすくなります。専門用語が多い記事で止まってしまう場合は、同じテーマの別の短い教材へ移って構いません。</p>
<p>難易度の目安は、英文を見たときに大まかな内容を説明できるかどうかです。ほとんどの文で辞書が必要なら、先に日本語の要点を読んでから取り組む方法もあります。</p>
<h2>聞く・解く・確認する</h2>
<ol><li><strong>まず音声だけで聞く。</strong>すべての単語ではなく、「誰が、何を、なぜ」を拾います。</li><li><strong>リスニング問題に答える。</strong>分からない箇所も、いったん自分の判断を置きます。</li><li><strong>英文と解答を確認する。</strong>聞き取れなかった1文を選び、音と文字を対応させます。</li><li><strong>もう一度聞く。</strong>選んだ文が、前より区切って聞こえるか確かめます。</li></ol>
<h2>1週間の使い方の一例</h2>
<table><thead><tr><th scope="col">日</th><th scope="col">取り組むこと</th></tr></thead><tbody>
<tr><th scope="row">1日目</th><td>教材Aの音声とリスニング問題。英文で答えの根拠を確認。</td></tr>
<tr><th scope="row">2日目</th><td>教材Aを再度聞き、覚えたい表現を1つ使って例文を書く。</td></tr>
<tr><th scope="row">3日目</th><td>教材Aの要点を日本語で一言、その後、英語1〜2文で説明する。</td></tr>
<tr><th scope="row">4日目</th><td>同じテーマの教材Bを聞き、共通する単語を探す。</td></tr>
<tr><th scope="row">5日目</th><td>教材Bのクイズと英文確認。必要なら音声を短く区切って復習。</td></tr>
<tr><th scope="row">6日目</th><td>教材AかBを、英文を見ずにもう一度聞く。</td></tr>
<tr><th scope="row">7日目</th><td>週の復習ページ、または学んだ教材で理解を振り返る。</td></tr>
</tbody></table>
<p>これは実施例です。忙しい日は音声だけにする、同じ教材を翌週まで使うなど、続けられる量に調整してください。特定の期間での上達や試験スコアを保証するものではありません。</p>
<h2>単語は「使われ方」と一緒に残す</h2>
<p>単語だけを一覧に写す代わりに、短い語の組み合わせを選びます。例えば <em>raise prices</em>（価格を上げる）や <em>cut costs</em>（費用を削減する）です。どんな主語と使われ、何を説明していたかも確認すると、次の記事で見つける手がかりになります。</p>
<h2>古いニュースも教材として使える</h2>
<p>過去の記事は、当時の状況を扱う英語教材です。日付を確認し、現在の政策・企業状況と混同しないようにしましょう。事実を調べる目的では、元記事や新しい一次情報も確認してください。</p>
HTML
        ),
        'listening-help' => array(
            'slug' => 'english-news-listening-practice',
            'title' => '英語ニュースが聞き取れないときの復習方法｜スクリプトの使い方',
            'excerpt' => '英語ニュースが聞き取れない原因を、単語・音・文の理解に分けて確認。スクリプトと短い聞き直しを使う具体的な復習手順を紹介します。',
            'topic' => '',
            'html' => <<<'HTML'
<p class="eel-lead">「分からなかった1文」から。</p>
<p>英語ニュースを最後まで聞いても内容が残らないとき、同じ音声を通しで何度も流すだけでは、どこで止まっているか分かりにくいものです。スクリプトを使い、分からなかった箇所を1文ずつ確かめてみましょう。</p>
<h2>まず、英文を見たら理解できるかを確認する</h2>
<dl><dt><strong>英文を読んでも意味が分からない</strong></dt><dd>知らない単語や文の構造が障害になっている可能性があります。語彙の意味、主語と動詞、何を説明する文なのかを先に確認します。</dd><dt><strong>読めば分かるのに、音では分からない</strong></dt><dd>音のつながりや語の区切りを確認する練習から始めます。分かったつもりの単語も、実際にどんな音になっているか聞き直します。</dd><dt><strong>1文は分かるが、話全体を追えない</strong></dt><dd>情報の整理に注目します。「出来事」「理由」「影響」の3つを、最初は日本語で短くメモして構いません。</dd></dl>
<h2>10分で取り組む復習手順</h2>
<ol><li><strong>1回聞いて大意をつかむ。</strong>知らない単語があっても、すぐには止めず、どんな話題か考えます。</li><li><strong>クイズに答えてみる。</strong>自信のない答えには印を付け、後で根拠を探します。</li><li><strong>聞き取れなかった1文を選ぶ。</strong>全文を書き取る必要はありません。短い部分を繰り返し使います。</li><li><strong>英文を見ながら音声を聞く。</strong>文字と音が対応したら、声に出して読み、音声に合わせてみます。</li><li><strong>英文を閉じてもう一度聞く。</strong>どの語まで聞き取れたか、最初の状態と比べます。</li></ol>
<p>教材の「聞く・解くモード」では英文や日本語解説を一時的に隠せます。確認したくなったら「全文を表示」へ戻せます。聞く前に内容を確認したい日には、最初から全文を読んでも大丈夫です。</p>
<h2>数字や固有名詞で止まったら</h2>
<p>企業名、地名、割合などは、話全体を追う途中で負担になることがあります。最初は「何かの数字が出てきた」と把握し、英文で確認してから、その数字が売上・物価・人数のどれを示すか整理してみましょう。</p>
<h2>聞き取れない日も、記録は小さく</h2>
<p>「今日はこの表現を音で確認した」と一つ残せれば、次の復習の出発点になります。教材の学習済みボタンは、自分で取り組んだ印です。正答率や習熟度の判定ではありません。</p>
<p>学習済みの印はこのブラウザだけに保存されます。別の端末とは同期せず、ブラウザの保存データを消すと印も消えます。</p>
<p>学習の参考：<a href="https://learnenglish.britishcouncil.org/free-resources/listening">British Council LearnEnglish — Listening</a>（英語）。レベル別の音声、理解度課題、スクリプトを使う教材もあります。</p>
HTML
        ),
        'inflation-words' => array(
            'slug' => 'inflation-news-english-vocabulary',
            'title' => 'インフレのニュースで使う英単語10選｜意味・例文と読み方の注意点',
            'excerpt' => 'inflation、wages、interest rateなど物価ニュースを読むための英単語10選。練習用例文と、物価上昇率の低下を読み違えないための注意点を解説します。',
            'topic' => 'prices',
            'html' => <<<'HTML'
<p class="eel-lead">物価のニュースを、語の組み合わせから。</p>
<p>物価の記事では、価格そのものと「価格が変わる速さ」を区別することが大切です。まずは、次の10語と一緒に使われる表現を確認しましょう。</p>
<p class="eel-note">以下の英文は練習用に作成した例です。実際の国・企業の経済状況を伝えるニュースではありません。</p>
<table><thead><tr><th scope="col">単語・表現</th><th scope="col">意味と練習用例文</th></tr></thead><tbody>
<tr><th scope="row">inflation</th><td>物価が全体として上がること。<br><em>Inflation affects household budgets.</em><br>インフレは家計に影響します。</td></tr>
<tr><th scope="row">price</th><td>個別の商品やサービスの価格。<br><em>The shop raised its prices.</em><br>その店は価格を上げました。</td></tr>
<tr><th scope="row">wages</th><td>仕事に対して支払われる賃金。<br><em>Workers are asking for higher wages.</em><br>労働者は賃金の引き上げを求めています。</td></tr>
<tr><th scope="row">purchasing power</th><td>お金で商品やサービスを買える力、購買力。<br><em>Higher prices can reduce purchasing power.</em><br>価格上昇は購買力を下げる可能性があります。</td></tr>
<tr><th scope="row">interest rate</th><td>借りたお金にかかる利息や預金の利息などを、割合で表した金利。<br><em>The report discusses changes in interest rates.</em><br>その報告書は金利の変化を論じています。</td></tr>
<tr><th scope="row">central bank</th><td>金融政策などを担う中央銀行。<br><em>The central bank published its forecast.</em><br>中央銀行は予測を公表しました。</td></tr>
<tr><th scope="row">consumer price index (CPI)</th><td>消費者が購入する商品やサービスの価格の動きをまとめた消費者物価指数。<br><em>The CPI measures changes in consumer prices.</em><br>CPIは消費者物価の変化を測ります。</td></tr>
<tr><th scope="row">demand</th><td>商品やサービスを買いたいという需要。<br><em>Demand for the product increased.</em><br>その商品の需要が増えました。</td></tr>
<tr><th scope="row">supply</th><td>供給される商品やサービス、またはその量。<br><em>The company increased its supply of parts.</em><br>その会社は部品の供給を増やしました。</td></tr>
<tr><th scope="row">cost of living</th><td>住居、食料、光熱費など、暮らしに必要な費用。<br><em>Families are concerned about the cost of living.</em><br>家族は生活費を心配しています。</td></tr>
</tbody></table>
<h2>「インフレが下がる」と「価格が下がる」は違う</h2>
<p><em>Inflation slowed.</em> は、一般に物価の上昇率が低下したことを表します。上昇率がプラスなら、価格水準は引き続き上がり得ます。「値下がりした」とすぐに置き換えないようにしましょう。</p>
<p>例えば、ある価格指数が100から105、翌年に107となる練習例を考えます。価格水準は105から107へ上がっていますが、上昇率は前の年より小さくなっています。実際の記事では、比較している期間や対象品目も確認してください。</p>
<h2>数字と一緒に見る3点</h2>
<ul><li><strong>何と比べているか：</strong>前年同月比か、前月比か。</li><li><strong>何を測っているか：</strong>特定の商品価格か、CPIなどの指数か。</li><li><strong>事実か予測か：</strong><em>rose</em>（上がった）と <em>is expected to rise</em>（上がると予想される）を区別する。</li></ul>
<p>単語を確認したら、物価・暮らしの教材を1本選び、これらの語や数字がどの文で使われているか探してみましょう。</p>
<p>用語の参考：<a href="https://www.bankofengland.co.uk/explainers/what-is-inflation">Bank of England — What is inflation?</a>。このページは英語学習用の解説で、個別の投資判断を案内するものではありません。</p>
HTML
        ),
    );
}
