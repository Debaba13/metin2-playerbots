<?php
	if(!isset($_SESSION['id'])) {
		header("Location: ?s=login");
		exit;
	} else {
?>
<div id="container">
	<?php include("pages/etc.php") ?>
	<div id="mainContent">
		<h1>Ejder Sikkesi Yükleme</h1>
		<div class="dynContent" style="position:relative">
				<font color="#996600;" size="3">
				<br /><p>Ejder Sikkelerini (ES) sunucuda oynayarak kazanırsın (görevler, etkinlikler).
				Ejder Nişanlarını (EN) bu mağazadaki her alışverişte otomatik olarak kazanırsın.<br />
				Daha fazla bilgi almak istersen yönetimle iletişime geç.
				</p><br />
				</font>
		</div>
		<div class="endContent"></div>
	</div>
</div>
<?php
	}
?>
