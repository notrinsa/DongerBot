<?php $json = json_decode(@file_get_contents("liste.json"), true); ?>
<?php ksort($json); ?>
<!DOCTYPE html>
	<html>
		<head>
			<title>!dongerbot ::</title>
			<!--Import Google Icon Font-->
			<link href="http://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
			<!--Import materialize.css-->
			<link type="text/css" rel="stylesheet" href="assets/css/materialize.min.css"  media="screen,projection"/>
			<link type="text/css" rel="stylesheet" href="assets/css/theme.css"  media="screen,projection"/>
			<!--Let browser know website is optimized for mobile-->
			<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
		</head>
		<body>
			<div class="container">
				<div class="section">
                    <ul class="tabs">
                        <?php foreach ($json as $category => $dongers) { ?>
                            <li class="tab col"><a href="#<?=$category;?>"><?=$category;?></a></li>
                        <?php } ?>
                    </ul>
                    <?php foreach ($json as $category => $dongers) { ?>
                        <?php ksort($dongers); ?>
                    <div id="<?=$category;?>" class="col s12">
                        <table class="highlight bordered">
                            <thead>
                                <tr>
                                    <th data-field="command">Commande</th>
                                    <th data-field="action">Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                <?php foreach ($dongers as $donger => $infos) { ?>
                                <tr><?php
                                    $commande = $infos['commande'];
                                    $action = $infos['action'];
                                    $args = $infos['args'] ? $infos['args'] : false;
                                    if ($args == 1) {
                                        $action = str_replace("%s", "<span class='nickname-blue'>{{ pseudo }}</span>", $action);
                                    } else if ($args == 2) {
                                        $action = str_replace("%s", "<span class='nickname-blue'>{{ texte }}</span>", $action);
                                    } else if ($args == 3) {
                                        $action = str_replace("{0}", "<span class='nickname-blue'>{{  }}</span>", $action);
                                        $action = str_replace("{1}", "<span class='nickname-blue'>{{  }}</span>", $action);
                                    }
                                    
                                    ?>
                                    <td class="command"><?=$commande;?></td>
                                    <td class="action"><?=$action;?></td>
                                </tr>
                                <?php } ?>
                            </tbody>
                        </table>
                    </div>
                    <?php } ?>
				</div>
			</div>

			<!--Import jQuery before materialize.js-->
			<script type="text/javascript" src="assets/js/jquery.min.js"></script>
			<script type="text/javascript" src="assets/js/materialize.min.js"></script>
		</body>
	</html>
