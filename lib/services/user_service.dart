// lib/services/user_service.dart
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter/foundation.dart';
import '../config/env.dart';
import 'auth_service.dart';

class UserService {
  static Future<bool> checkFaceRegistrationStatus() async {
    debugPrint('================== USER SERVICE - CHECK FACE STATUS ==================');
    try {
      final token = await AuthService.getToken();
      if (token == null) {
        throw Exception('No authentication token found');
      }

      final response = await http.get(
        Uri.parse('${Env.apiUrl}/api/users/register-face-status'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      debugPrint('Response status: ${response.statusCode}');
      debugPrint('Response body: ${response.body}');

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['status'] == 'success') {
          return data['data']['feature_status'] == 'yes';
        }
      }
      return false;
    } catch (e) {
      debugPrint('Error checking face status: $e');
      return false;
    } finally {
      debugPrint('=========================================================');
    }
  }
}