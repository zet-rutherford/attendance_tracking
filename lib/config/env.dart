class Env {
  static const String apiUrl = String.fromEnvironment('API_URL',
      defaultValue: 'http://172.16.80.52:8889');
}