use liboxia::client::Client;
use liboxia::client_builder::OxiaClientBuilder;
use testcontainers::ImageExt;
use testcontainers::core::logs::consumer;
use testcontainers::runners::AsyncRunner;
use testcontainers_oxia::standalone::OxiaStandalone;

#[tokio::main]
async fn main() {
    let container = OxiaStandalone::default()
        .with_log_consumer(
            consumer::logging_consumer::LoggingConsumer::default()
                .with_stderr_level(log::Level::Info)
                .with_stdout_level(log::Level::Info),
        )
        .start()
        .await
        .unwrap();

    let stdout = String::from_utf8(container.stdout_to_vec().await.unwrap()).unwrap();
    println!("{}", stdout);
    let address = format!(
        "127.0.0.1:{}",
        container.get_host_port_ipv4(6648).await.unwrap()
    );
    let client = OxiaClientBuilder::default()
        .service_address(address)
        .build()
        .await
        .unwrap();

    let key = "test_key".to_string();
    let payload = "test_payload".to_string().into_bytes();
    let put_result = client.put(key.clone(), payload).await.unwrap();
    println!("put result: {:?}", put_result);
    let get_result = client.get(key).await.unwrap();
    println!("get result: {:?}", get_result);
}
