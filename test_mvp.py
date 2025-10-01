"""
Teste simples para MVP
"""
import requests
import sys


def test_health_endpoint():
    """Testa endpoint de health"""
    try:
        response = requests.get("http://localhost:8082/health")
        print(f"✅ Health Check: {response.status_code}")
        if response.json():
            print(f"✅ Response: {response.json()['status']}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        return False


def test_hello_endpoint():
    """Testa endpoint hello world"""
    try:
        response = requests.get("http://localhost:8082/hello")
        print(f"✅ Hello Endpoint: {response.status_code}")
        if response.json():
            print(f"✅ Message: {response.json()['message']}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Hello Endpoint Failed: {e}")
        return False


def test_root_endpoint():
    """Testa endpoint raiz"""
    try:
        response = requests.get("http://localhost:8082/")
        print(f"✅ Root Endpoint: {response.status_code}")
        if response.json():
            print(f"✅ Service: {response.json()['service']}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Root Endpoint Failed: {e}")
        return False


def test_swagger_docs():
    """Testa documentação Swagger"""
    try:
        response = requests.get("http://localhost:8082/docs")
        print(f"✅ Swagger Docs: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Swagger Docs Failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Executando testes básicos da API MVP\n")
    
    tests = [
        test_health_endpoint,
        test_hello_endpoint,
        test_root_endpoint,
        test_swagger_docs
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todos os testes passaram! API MVP funcionando.")
        sys.exit(0)
    else:
        print("⚠️  Alguns testes falharam. Verifique se a API está rodando.")
        sys.exit(1)