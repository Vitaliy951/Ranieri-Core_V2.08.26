Применение манифестов

    Создайте namespace и секреты (заполнив реальными данными):
    bash

    kubectl apply -f k8s/prod/namespace.yaml
    kubectl apply -f k8s/staging/namespace.yaml
    kubectl apply -f k8s/prod/secret.yaml
    kubectl apply -f k8s/staging/secret.yaml

    Примените остальные ресурсы:
    bash

    kubectl apply -f k8s/prod/
    kubectl apply -f k8s/staging/

    Проверьте статус:
    bash

    kubectl get pods -n ranieri-prod
    kubectl get pods -n ranieri-staging

📌 Важные замечания

    Имена контейнеров в deployment должны строго совпадать с теми, что указаны в пайплайне (ranieri-api). Это критично для команды kubectl set image ....

    Image Pull Secret (yandex-registry-secret) должен быть создан заранее для доступа к приватному Docker registry (если используется). Создать его можно командой:
    bash

    kubectl create secret docker-registry yandex-registry-secret \
      --docker-server=cr.yandex \
      --docker-username=oauth \
      --docker-password=$YANDEX_CLOUD_OAUTH_TOKEN \
      -n ranieri-prod

    (аналогично для staging).

    ClickHouse должен быть развёрнут отдельно (например, как StatefulSet) в каждом namespace, либо использоваться внешний кластер. В конфигмапах указаны внутренние DNS-имена.

    Для production рекомендуется использовать 3 реплики для отказоустойчивости, для staging достаточно 1.

    В ingress можно добавить cert-manager для автоматического получения Let's Encrypt сертификатов.

Все файлы готовы к использованию. Убедитесь, что ваши кластеры имеют доступ к Yandex Container Registry, и секреты заполнены корректно. 
