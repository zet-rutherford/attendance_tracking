// lib/services/auth_service.dart
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../config/env.dart';
import 'package:shared_preferences/shared_preferences.dart';  // Fixed import
import '../config/env.dart';
import 'package:flutter/foundation.dart';

class UserInfo {
  final int id;
  final String username;
  final String fullname;
  final String email;

  UserInfo({
    required this.id,
    required this.username,
    required this.fullname,
    required this.email,
  });

  factory UserInfo.fromJson(Map<String, dynamic> json) {
    return UserInfo(
      id: json['id'],
      username: json['username'],
      fullname: json['fullname'],
      email: json['email'],
    );
  }
}

class AuthService {
  static const String _tokenKey = 'auth_token';
  static const String _tokenExpiryKey = 'token_expiry';
  static const String _userInfoKey = 'user_info';

  static Future<void> saveUserInfo(UserInfo userInfo) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_userInfoKey, json.encode({
      'id': userInfo.id,
      'username': userInfo.username,
      'fullname': userInfo.fullname,
      'email': userInfo.email,
    }));
  }

  static Future<UserInfo?> getUserInfo() async {
    final prefs = await SharedPreferences.getInstance();
    final userInfoString = prefs.getString(_userInfoKey);
    if (userInfoString != null) {
      final userInfoMap = json.decode(userInfoString);
      return UserInfo.fromJson(userInfoMap);
    }
    return null;
  }

  static Future<void> saveToken(String token) async {
    debugPrint('================== AUTH SERVICE - SAVE TOKEN ==================');
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_tokenKey, token);
      debugPrint('Token saved to SharedPreferences');

      final parts = token.split('.');
      if (parts.length == 3) {
        final payload = json.decode(
            utf8.decode(base64Url.decode(base64Url.normalize(parts[1])))
        );
        if (payload['exp'] != null) {
          await prefs.setInt(_tokenExpiryKey, payload['exp']);
          debugPrint('Token expiry saved: ${payload['exp']}');
        }
      }
    } catch (e) {
      debugPrint('Error saving token: $e');
      rethrow;
    } finally {
      debugPrint('======================================================');
    }
  }

  static Future<String?> getToken() async {
    debugPrint('================== AUTH SERVICE - GET TOKEN ==================');
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString(_tokenKey);
    debugPrint('Token found: ${token != null}');
    if (token != null) {
      debugPrint('Token: $token');
    } else {
      debugPrint('No token found in SharedPreferences');
    }
    debugPrint('=========================================================');
    return token;
  }

  static Future<void> removeToken() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
    await prefs.remove(_tokenExpiryKey);
  }

  static Future<bool> isTokenExpired() async {
    final prefs = await SharedPreferences.getInstance();
    final expiry = prefs.getInt(_tokenExpiryKey);
    if (expiry == null) return true;

    return DateTime.fromMillisecondsSinceEpoch(expiry * 1000)
        .isBefore(DateTime.now());
  }

  static Future<Map<String, dynamic>> login(String username, String password) async {
    debugPrint('================== AUTH SERVICE - LOGIN ==================');
    try {
      final response = await http.post(
        Uri.parse('${Env.apiUrl}/api/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'username': username,
          'password': password,
        }),
      );

      debugPrint('Login response status: ${response.statusCode}');
      debugPrint('Login response body: ${response.body}');

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['data'] != null) {
          if (data['data']['access_token'] != null) {
            await saveToken(data['data']['access_token']);
          }
          if (data['data']['user'] != null) {
            await saveUserInfo(UserInfo.fromJson(data['data']['user']));
          }
        }
        return data;
      } else {
        debugPrint('Login failed with status: ${response.statusCode}');
        throw Exception('Login failed: ${response.body}');
      }
    } catch (e) {
      debugPrint('Error during login: $e');
      rethrow;
    } finally {
      debugPrint('==================================================');
    }
  }

  static Future<void> removeUserInfo() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_userInfoKey);
  }

  static Future<void> logout() async {
    final token = await getToken();
    if (token == null) return;

    try {
      await http.post(
        Uri.parse('${Env.apiUrl}/api/auth/logout'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );
    } finally {
      await removeToken();
      await removeUserInfo();
    }
  }
}