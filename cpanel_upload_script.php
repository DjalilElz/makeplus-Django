<?php
/**
 * File Upload API for Django
 * Place this file at: /home/wemaszvr/public_html/media/upload.php
 * 
 * Security: Uses secret key to prevent unauthorized uploads
 */

// Configuration
define('UPLOAD_SECRET_KEY', 'iuQP44jUBlvF0_B1fvp4SKsbT9-fb7VKf3YJXKunJAc');
define('BASE_UPLOAD_DIR', __DIR__);
define('MAX_FILE_SIZE', 50 * 1024 * 1024); // 50MB

// Enable error reporting for debugging (disable in production)
error_reporting(E_ALL);
ini_set('display_errors', 1);
ini_set('log_errors', 1);

// Set JSON response header
header('Content-Type: application/json');

// CORS headers (allow requests from your Django app)
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, X-Upload-Key');

// Handle preflight OPTIONS request
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// Only allow POST requests
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed', 'method' => $_SERVER['REQUEST_METHOD']]);
    exit;
}

// Verify secret key
$provided_key = $_POST['key'] ?? $_SERVER['HTTP_X_UPLOAD_KEY'] ?? '';
if ($provided_key !== UPLOAD_SECRET_KEY) {
    http_response_code(401);
    echo json_encode(['error' => 'Unauthorized', 'provided' => $provided_key]);
    exit;
}

// Check if file was uploaded
if (!isset($_FILES['file']) || $_FILES['file']['error'] !== UPLOAD_ERR_OK) {
    http_response_code(400);
    echo json_encode(['error' => 'No file uploaded or upload error', 'files' => $_FILES]);
    exit;
}

// Get file info
$file = $_FILES['file'];
$file_path = $_POST['path'] ?? '';

// Validate file path (prevent directory traversal)
if (empty($file_path) || strpos($file_path, '..') !== false) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid file path']);
    exit;
}

// Check file size
if ($file['size'] > MAX_FILE_SIZE) {
    http_response_code(413);
    echo json_encode(['error' => 'File too large']);
    exit;
}

// Create directory if it doesn't exist
$target_dir = BASE_UPLOAD_DIR . '/' . dirname($file_path);
if (!is_dir($target_dir)) {
    if (!mkdir($target_dir, 0755, true)) {
        http_response_code(500);
        echo json_encode(['error' => 'Failed to create directory', 'dir' => $target_dir]);
        exit;
    }
}

// Move uploaded file
$target_file = BASE_UPLOAD_DIR . '/' . $file_path;
if (move_uploaded_file($file['tmp_name'], $target_file)) {
    // Set file permissions
    chmod($target_file, 0644);
    
    // Return success response
    http_response_code(200);
    echo json_encode([
        'success' => true,
        'path' => $file_path,
        'url' => 'https://wemakeplus.com/media/' . $file_path,
        'size' => filesize($target_file)
    ]);
} else {
    http_response_code(500);
    echo json_encode(['error' => 'Failed to save file']);
}
?>
