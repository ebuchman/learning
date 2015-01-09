<?php

function handleRequest(){
    // error_log prints stuff to the terminal
    error_log("this is captain");

    // grab the GET variable from the ajax request
    $codevariable = $_GET["stuff"];

    // print the variable value locally
    error_log($codevariable);

    $ch = curl_init();
    $s = "https://ajax.googleapis.com/ajax/services/search/web?v=1.0&q=".$codevariable;
    curl_setopt($ch, CURLOPT_URL, $s);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, TRUE);
    curl_setopt($ch, CURLOPT_HEADER, FALSE);
    //curl_setopt($ch, CURLOPT_POST, TRUE);
    //curl_setopt($ch, CURLOPT_POSTFIELDS, "{ \"last_name\": \"".$lastname."\" }");
    //curl_setopt($ch, CURLOPT_HTTPHEADER, array("Content-Type: application/json"));
    $response = curl_exec($ch);
    curl_close($ch);
    error_log($response);
    $json_response = json_decode($response, true);
    echo $response; //$json_response;
    // echo responds to the ajax request
    //echo "hi nikki isnt this fun ".$codevariable." fun fun";

}

handleRequest()



?>
