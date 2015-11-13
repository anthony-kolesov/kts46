# Введение #

Здесь содержится список проблем, решённых в ходе разработки системы. Этот список нужен исключительно для того, чтобы на защите было понятно, что именно решено и сделано, потому что в конце всё сделанное будет казаться лёгким и очевидным :)


# Инфраструктура #

Система разбита на ряд компонентов, которые могут распологаться в том числе и на разных машинах. Для коммуникации используются различные протоколы. Главная причина разбиения на независимые компоненты - возможность их выполнения на разных компьютерах (при необходимости), меньшая зависимость частей симулирующей системы друг от друга, большая надёжность системы.

В основе всего лежит (точнее должен лежать) компонент ядра. Название не придумано, компонент не реализован пока, по сути жить всё может и без него, он нужен для централизованного управления. Этот компонент должен уметь запускать остальные компоненты, перезапускать их при необходимости, и делать что-нибудь ещё, что может потребоваться. Таким образом, например на все машины будет ставится полный набор компонентов системы, а то, какую роль эта машина выполняет и, следовательно, что нужно запускать, будет зависеть от конфигурации ядра. Теоретически можно сделать так, чтобы ядро получало команды от "центра управления" и динамически изменяло конфигурацию системы. Следует ещё обдумать нужно ли это вообще и стоит ли затрачиваемых усилий.

**Планировщик** (scheduler, scheduler.py) - из существующих является центральным компонентом, который управляет общими ресурсами, кроме БД. По сути это менеджер общих ресурсов из Python. Строго говоря он ничего не планирует (возможно, следует изменить название), он получает от клиента команду на добавление задания в список выполнения и выдаёт эти задания исполнителям. На данный момент планировщик не заботится о том, чтобы в очереди не оказалось дублирующих заданий, а следовало бы (см http://code.google.com/p/kts46/issues/detail?id=13). Планировщик никак не контролирует, чтобы выданное исполнителю задание было исполнено. Этим должен заниматься контролёр. Правда тогда выходит, что контролёр и исполнителю используют один и тот же интерфейс с одним и тем же ключом безопасности. Потенциально любой идиот тогда сможет командовать планировщиком как захочет. Оно нам надо? С другой стороны защитой информации занимаются на другой кафедре, потому сидеть и разрабатывать чересчур мощное средство обороны будет излишне.

**Исполнитель, агент** (worker, worker.py) - выполняет непосредственно симуляцию и подсчёт статистики. Получает задание от планировщика, выполняет, сохраняет результат в базу данных и рапортует планировщику о выполнении задания. Общается только с планировщиком, используя мультипоточный менеджер общих ресурсов из стандартной библиотеки Python.

**XML-RPC server** (rpc\_server.py) - интерфейс системы. позволяет создавать проекты, добавлять задания и ставить их на выполнение. Внешний мир общается с ним посредством XML-RPC (как и следует из названия).

**XML-RPC client** (rpc\_client.py) - небольшая программка, работающая из командной строки для общения с RPC сервером.


# База данных #

В качестве хранилища данных используется CouchDB, который живёт своей жизнью, независимо от остальных.