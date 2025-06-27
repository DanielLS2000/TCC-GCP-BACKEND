@echo off
echo 🚀 Iniciando o processo de deploy...

echo.
echo 📦 Construindo a imagem Docker: daniel20000/inventory:latest
docker build -t daniel20000/inventory:latest . || exit /b

echo.
echo ⬆️ Enviando a imagem para o Docker Hub...
docker push daniel20000/inventory:latest || exit /b

echo.
echo 🔄 Reiniciando o deployment 'inventory' no Kubernetes...
kubectl rollout restart deployment inventory || exit /b

echo.
echo ✅ Deploy concluído com sucesso!