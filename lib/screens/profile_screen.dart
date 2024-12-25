// lib/screens/profile_screen.dart
import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import '../services/user_service.dart';
import 'package:camera/camera.dart';
import 'login_screen.dart';
import 'dart:io';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {

  bool _isLoading = false;
  bool _isCameraActive = false;
  bool _isProcessing = false;
  bool _hasFaceRegistered = false;
  UserInfo? _userInfo;

  // Camera related variables
  List<CameraDescription>? cameras;
  CameraController? _cameraController;
  File? _capturedImage;

  @override
  void initState() {
    super.initState();
    _loadUserInfo();
    _checkFaceStatus();
    _initCamera();
  }

  Future<void> _loadUserInfo() async {
    final userInfo = await AuthService.getUserInfo();
    if (mounted) {
      setState(() {
        _userInfo = userInfo;
      });
    }
  }

  Future<void> _checkFaceStatus() async {
    setState(() {
      _isLoading = true;
    });
    try {
      final hasRegistered = await UserService.checkFaceRegistrationStatus();
      setState(() {
        _hasFaceRegistered = hasRegistered;
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error checking face status: $e')),
        );
      }
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _logout() async {
    try {
      await AuthService.logout();
      if (mounted) {
        Navigator.pushAndRemoveUntil(
          context,
          MaterialPageRoute(builder: (context) => const LoginScreen()),
              (route) => false,
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Logout failed: $e')),
        );
      }
    }
  }

  Future<void> _initCamera() async {
    try {
      cameras = await availableCameras();
      if (cameras != null && cameras!.isNotEmpty) {
        // Try to find front camera
        final frontCamera = cameras!.firstWhere(
              (camera) => camera.lensDirection == CameraLensDirection.front,
          orElse: () => cameras!.first,
        );

        _cameraController = CameraController(
          frontCamera,
          ResolutionPreset.medium,
          enableAudio: false,
        );

        await _cameraController!.initialize();
        if (mounted) {
          setState(() {});
        }
      }
    } catch (e) {
      debugPrint('Error initializing camera: $e');
    }
  }

  Future<void> _captureAndRegisterFace() async {
    if (_cameraController == null || !_cameraController!.value.isInitialized) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Camera not initialized')),
      );
      return;
    }

    setState(() => _isProcessing = true);

    try {
      // Capture image
      final XFile image = await _cameraController!.takePicture();
      setState(() => _capturedImage = File(image.path));

      // Send to server
      final response = await UserService.registerFace(image.path);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(response['message'] ?? 'Face registered successfully')),
        );
        // Check face status again after registration
        _checkFaceStatus();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isProcessing = false;
          _isCameraActive = false;
        });
      }
    }
  }

  void _showChangePasswordDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Change Password'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              obscureText: true,
              decoration: const InputDecoration(
                labelText: 'Current Password',
              ),
            ),
            const SizedBox(height: 8),
            TextField(
              obscureText: true,
              decoration: const InputDecoration(
                labelText: 'New Password',
              ),
            ),
            const SizedBox(height: 8),
            TextField(
              obscureText: true,
              decoration: const InputDecoration(
                labelText: 'Confirm New Password',
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              // TODO: Implement password change logic
              Navigator.pop(context);
            },
            child: const Text('Change Password'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isCameraActive && _cameraController?.value.isInitialized == true) {
      return Scaffold(
        appBar: AppBar(
          title: const Text('Register Face'),
          centerTitle: true,
        ),
        body: Stack(
          alignment: Alignment.center,
          children: [
            CameraPreview(_cameraController!),
            if (_isProcessing)
              const CircularProgressIndicator(),
            Positioned(
              bottom: 20,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  ElevatedButton(
                    onPressed: _isProcessing ? null : _captureAndRegisterFace,
                    child: const Text('Capture Photo'),
                  ),
                  const SizedBox(width: 20),
                  ElevatedButton(
                    onPressed: () => setState(() => _isCameraActive = false),
                    child: const Text('Cancel'),
                  ),
                ],
              ),
            ),
          ],
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Profile'),
        centerTitle: true,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            const CircleAvatar(
              radius: 50,
              child: Icon(Icons.person, size: 50),
            ),
            const SizedBox(height: 20),
            Text(
              _userInfo?.fullname ?? 'Loading...',
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 10),
            Text(
              _userInfo?.username ?? '',
              style: const TextStyle(
                fontSize: 16,
                color: Colors.grey,
              ),
            ),
            Text(
              _userInfo?.email ?? '',
              style: const TextStyle(
                fontSize: 16,
                color: Colors.grey,
              ),
            ),
            const SizedBox(height: 30),
            ListTile(
              leading: const Icon(Icons.access_time),
              title: const Text('Attendance History'),
              onTap: () {
                // TODO: Navigate to attendance history
              },
            ),
            ListTile(
              leading: const Icon(Icons.face),
              title: const Text('Register Face'),
              subtitle: Text(
                _hasFaceRegistered ? 'Face already registered' : 'Face not registered',
                style: TextStyle(
                  color: _hasFaceRegistered ? Colors.green : Colors.red,
                ),
              ),
              onTap: _hasFaceRegistered ? null : () {
                setState(() => _isCameraActive = true);
              },
              enabled: !_hasFaceRegistered,
              trailing: _isLoading ?
              const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2),
              ) :
              Icon(
                _hasFaceRegistered ? Icons.check_circle : Icons.arrow_forward_ios,
                color: _hasFaceRegistered ? Colors.green : null,
              ),
            ),
            ListTile(
              leading: const Icon(Icons.lock),
              title: const Text('Change Password'),
              onTap: () => _showChangePasswordDialog(context),
            ),
            const Spacer(),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _logout,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: const Text(
                  'Logout',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _cameraController?.dispose();
    super.dispose();
  }
}