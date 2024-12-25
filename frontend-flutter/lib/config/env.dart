class Env {
  static const String apiUrl = String.fromEnvironment('API_URL',
      defaultValue: 'http://192.168.1.109:8889');
}