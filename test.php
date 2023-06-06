<?php

include ("./utilities/HelperFunctions.php");
include ("./utilities/db.php");

$SCRIPTS_PATH = "/var/www/html/visualization_scripts/";


$hf = new HelperFunctions(getenv("KEYCLOAK_BASE_URL"), getenv("KEYCLOAK_ADMIN_USR"), getenv("KEYCLOAK_ADMIN_PWD"), getenv("KEYCLOAK_CLIENT_ID"), getenv("KEYCLOAK_CLIENT_SECRET"), getenv("KEYCLOAK_REALM_NAME"));

// respond to preflights
if ($_SERVER['REQUEST_METHOD'] == 'OPTIONS') {
    // return only the headers and not the content
    // only allow CORS if we're doing a GET - i.e. no saving for now.
    if (isset($_SERVER['HTTP_ACCESS_CONTROL_REQUEST_METHOD']) && $_SERVER['HTTP_ACCESS_CONTROL_REQUEST_METHOD'] == 'POST') {
        header('Access-Control-Allow-Origin: *');
        header('Access-Control-Allow-Headers: X-Requested-With');
    }
    exit;
}

if ($_SERVER['REQUEST_METHOD'] != 'POST') {
   $response = array(
	'status' => 'Error',
	'info' => 'Method not supported'
   );
   $hf->returnResponse(405, $response);
}

$entityBody = file_get_contents('php://input');
$jsonBody = json_decode($entityBody);
$userId = $jsonBody->userId;


if (empty($userId)) {
    $response = array(
 	'status' => 'Error',
 	'info' => 'empty user id not allowed'
    );
    $hf->returnResponse(400, $response);
}

# get authentication header from 
$token = '';
$headers = getallheaders();
$headers = array_change_key_case($headers, CASE_LOWER);
if (array_key_exists('authorization', $headers)) {
    $authHeader = $headers['authorization'];
    $headerParts = explode(' ', $authHeader);
    if ((count($headerParts) == 2) && (strcasecmp($headerParts[0], "Bearer") == 0))
      $token = $headerParts[1];
}
if (empty($token)) {
     $response = array(
        'status' => 'Error',
        'info' => "Authorization header not valid or empty user token");
     $hf->returnResponse(401, $response);
}

# check if payload userId parameter matches the token subject
$sub = $hf->tokenIntrospect($token);
if (($sub == -1) || ($sub != $userId)) {
     $response = array(
        'status' => 'Error',
        'info' => "User id in payload does not match authorization header id");
     $hf->returnResponse(401, $response);
}

if (empty($userId)) {
   $response = array(
 	'status' => 'Error',
 	'info' => 'empty user id not allowed'
   );
   $hf->returnResponse(400, $response);
}


// Execute the script to generate the heatmap file
$pythonScriptPath = $SCRIPTS_PATH . "script1.py";
$userId = "b98bf30f-ebec-48b4-b5a3-e76f9f292f6f";
$output = shell_exec("python3 {$pythonScriptPath} \"{$userId}\" 2>&1");

// Extract the path to the generated heatmap file from the script output
$heatmapFilePath = trim($output);

$response = array(
    'status' => 'Success',
);

$hf->returnFileResponse(200, $response, $heatmapFilePath);


?>
