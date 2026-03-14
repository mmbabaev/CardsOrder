Как начать работать с Monium
Статья создана

Yandex Cloud
Обновлена 3 марта 2026 г.
Monium — платформа для сбора метрик, логов и трейсов из Yandex Cloud, других облаков или вашей инфраструктуры.

Эта инструкция поможет передать телеметрию из вашего или демонстрационного приложения через OTel Collector и просмотреть ее в Monium.

Начать работу с метриками Yandex Cloud можно с помощью раздела Начало работы с метриками ресурсов Yandex Cloud.

Чтобы начать работу с телеметрией приложения в Monium:

Подготовьте облако к работе.
Создайте сервисный аккаунт и API-ключ.
Настройте передачу телеметрии из вашего приложения или демо-приложения.

Если у вас уже настроена отправка телеметрии в формате OTLP, укажите параметры подключения к Monium.

Просмотрите данные в Monium.
Подготовьте облако к работе

Войдите в консоль управления или зарегистрируйтесь. Если вы еще не зарегистрированы, перейдите в консоль управления и следуйте инструкциям.
На странице Yandex Cloud Billing убедитесь, что у вас подключен платежный аккаунт и он находится в статусе ACTIVE или TRIAL_ACTIVE. Если платежного аккаунта нет, создайте его.

Если у вас есть активный платежный аккаунт, вы можете создать или выбрать каталог, в котором будет работать ваша инфраструктура, на странице облака.

Подробнее об облаках и каталогах.

Создайте сервисный аккаунт и API-ключ

В консоли управления перейдите в каталог, в котором будет храниться телеметрия.
Перейдите в сервис Identity and Access Management.
Нажмите кнопку Создать сервисный аккаунт.
Введите имя сервисного аккаунта, например monium-ca.
Нажмите кнопку  Добавить роль и добавьте monium.telemetry.writer.
Если вы планируете передавать только некоторые типы данных, вместо monium.telemetry.writer выберите одну или несколько ролей: monium.metrics.writer, monium.logs.writer, monium.traces.writer.

Нажмите кнопку Создать.
Выберите созданный аккаунт в списке.
На панели сверху нажмите кнопку  Создать новый ключ и выберите пункт Создать API-ключ.
Выберите Область действия — yc.monium.telemetry.write.
(Опционально) Укажите Срок действия.
Нажмите кнопку Создать.
Сохраните секретный ключ, он понадобится на следующем шаге.
Настройте передачу телеметрии из вашего приложения

Если у вас нет готового приложения, воспользуйтесь демонстрационным.

В Monium телеметрия организована в иерархии «проект → кластер → сервис». Данные для каждой пары «сервис-кластер» распределяются по отдельным шардам.

Установите переменные окружения:
MONIUM_PROJECT — имя проекта Monium.

По умолчанию при создании облака и каталога создаются два проекта: cloud__<идентификатор_облака> и folder__<идентификатор_каталога>. Также можно создать другие проекты.

Для тестирования работы с Monium можно указать проект каталога, например, folder__b1g86q4m5vej********.

При вводе вручную учитывайте, что после folder следуют два нижних подчеркивания.

MONIUM_API_KEY — API-ключ.
Настройте отправку телеметрии из приложения в формате OTLP:
Установите агента для автоинструментации, который автоматически собирает часть телеметрии и передает в OTLP.
Добавьте OpenTelemetry SDK в ваше приложение.
Установите OTel Collector.

Данные можно отправлять в Monium без агента, напрямую из OpenTelemetry SDK.

В файле конфигурации otel-collector.yaml настройте передачу данных в Monium.

Пример минимальной конфигурации otel-collector.yaml:

receivers:       
  otlp:          # Тип приемника — OTLP
    protocols:   # Протоколы, которые слушает Collector
      grpc:      # gRPC, порт 4317 по умолчанию
      http:      # HTTP, порт 4318 по умолчанию

processors:
  cumulativetodelta:
  batch:

exporters:       # Подключение к Monium
  otlp/monium:
    compression: zstd
    endpoint: ingest.monium.yandex.cloud:443
    headers:
      Authorization: "Api-Key ${env:MONIUM_API_KEY}"
      x-monium-project: "${env:MONIUM_PROJECT}"

service:         
  pipelines:
    metrics:                 # Передача метрик
      receivers: [ otlp ]
      processors: [ batch, cumulativetodelta ]
      exporters: [ otlp/monium ]
    traces:                  # Передача трейсов
      receivers: [ otlp ]
      processors: [ batch ]
      exporters: [ otlp/monium ]
    logs:                    # Передача логов
      receivers: [ otlp ]
      processors: [ batch ]
      exporters: [ otlp/monium ]

Установите переменные окружения для распределения данных по шардам в Monium:
OTEL_SERVICE_NAME — имя вашего приложения или сервиса.
(Опционально) OTEL_RESOURCE_ATTRIBUTES="cluster=my-cluster" — имя инсталляции, в которой работает приложение (например, боевое и тестовое окружение). По умолчанию cluster=default.
Запустите приложение и начните отправлять телеметрию.
Параметры подключения к Monium и распределение данных

Если в вашем приложении уже была настроена отправка телеметрии, укажите параметры:

Авторизация — API-ключ.
Эндпоинт — ingest.monium.yandex.cloud:443.
В заголовке: параметр x-monium-project=folder__<идентификатор_каталога>.
В атрибутах ресурса OTEL_RESOURCE_ATTRIBUTES: cluster или deployment.name и service или service.name.
Все метрики, логи, трейсы в Monium имеют обязательные метки project, cluster и service. Эти метки формируют ключ шарда.

При поставке телеметрии в формате OpenTelemetry значения ключевых атрибутов определяются следующим образом:

Приоритетнее — значения, заданные через HTTP или gRPC заголовки.
Затем — значения, заданные в ресурсных атрибутах тела запроса с ключами cluster, service.
Затем — значения, заданные в ресурсных атрибутах, рекомендуемые семантической конвенцией OpenTelemetry.
Иначе проставляется значение по умолчанию.
Имя проекта проставляется только из заголовка. Алгоритм определения ключа шарда представлен в таблице ниже.

заголовок
собственный атрибут ресурса
стандартный атрибут ресурса
значение по умолчанию
x-monium-project
—
—
—
x-monium-cluster
cluster
deployment.name
default
x-monium-service
service
service.name, k8s.deployment.name, k8s.namespace.name
default
Просмотрите данные в Monium

На главной странице Monium слева выберите Шарды.
В списке выберите шард с названием вашего сервиса.

Имя шарда формируется как <имя_проекта>_<имя_кластера>_<имя_сервиса>, например folder__b1g86q4m5vej********_default_spring-petclinic.

Чтобы посмотреть отдельный тип данных, слева выберите:
Метрики.

В строке запроса последовательно выберите project, cluster, service и нажмите Выполнить запрос.

Подробнее о работе с метриками.

Логи.

В строке запроса последовательно выберите project, cluster, service и нажмите Выполнить запрос.

Подробнее о работе с логами.

Трейсы.

В строке запроса последовательно выберите project и service и нажмите Выполнить.

Подробнее о работе с трейсами.

Примечание

Учитывайте, что данные в Monium появляются не сразу, а с задержкой, поскольку Otel Collector начинает отправку данных через 60 секунд.
Чтобы использовать полученные данные, вы можете создавать дашборды и алерты.

Пример настройки демонстрационного приложения

В этом примере вы установите приложение Spring PetClinic и настроите отправку телеметрии в Monium.

Установите Git и Java, подходящие для вашей ОС. Например:
sudo apt update
sudo apt install -y git openjdk-17-jdk

Скачайте и установите OTel Collector, подходящий для вашей ОС. Например:
wget https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v144.0/otelcol-linux_amd64.tar.gz
tar xvf otelcol-linux_amd64.tar.gz

Установите переменные окружения:
export MONIUM_PROJECT=folder__<идентификатор_каталога>
export MONIUM_API_KEY=<api_ключ>

Создайте файл otel-collector.yaml и скопируйте в него содержимое:
receivers:
  otlp:
    protocols:
      grpc:
      http:

exporters:
  otlp_grpc/monium:
    compression: zstd
    endpoint: ingest.monium.yandex.cloud:443
    headers:
      Authorization: "Api-Key ${env:MONIUM_API_KEY}"
      x-monium-project: "${env:MONIUM_PROJECT}"
    sending_queue:
      batch:

service:
  pipelines:
    metrics:
      receivers: [ otlp ]
      exporters: [ otlp_grpc/monium ]
    traces:
      receivers: [ otlp ]
      exporters: [ otlp_grpc/monium ]
    logs:
      receivers: [ otlp ]
      exporters: [ otlp_grpc/monium ]
  telemetry:
    metrics:
      level: normal
      readers:
        - periodic:
            exporter:
              otlp:
                protocol: http/protobuf
                endpoint: http://localhost:4318
            interval: 30000
            timeout: 5000

Запустите OTel Collector:

./otelcol-linux_amd64 --config otel-collector.yaml

Collector начнет слушать порты 4317 (gRPC) и 4318 (HTTP).

Скачайте и соберите Spring PetClinic:
git clone https://github.com/spring-projects/spring-petclinic
cd spring-petclinic
./mvnw -DskipTests package

Скачайте OpenTelemetry Java-агент:
curl -L -o opentelemetry-javaagent.jar \
https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/latest/download/opentelemetry-javaagent.jar

Запустите приложение с Java-агентом, который будет передавать телеметрию в OTel Collector:
OTEL_SERVICE_NAME=spring-petclinic \
OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE="delta" \
java -javaagent:./opentelemetry-javaagent.jar -jar target/*.jar

Откройте сайт Spring PetClinic http://localhost:8080 и выполняйте в нем действия пользователей.
После настройки просмотрите телеметрию в Monium.

См. также

Начало работы с метриками
Начало работы с логами
Начало работы с трейсами
Создание дашборда
Создание алерта
Способы поставки телеметрии
