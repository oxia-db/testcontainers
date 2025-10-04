use std::borrow::Cow;
use testcontainers::Image;
use testcontainers::core::{ContainerPort, WaitFor};

const EXTERNAL_PORT: ContainerPort = ContainerPort::Tcp(6648);
const INTERNAL_PORT: ContainerPort = ContainerPort::Tcp(6649);

#[derive(Debug, Clone)]
pub struct OxiaStandalone {
    pub image_name: String,
    pub tag: String,
    pub log_level: String,
}

impl Default for OxiaStandalone {
    fn default() -> Self {
        Self {
            image_name: "oxia/oxia".to_string(),
            tag: "latest".to_string(),
            log_level: "info".to_string(),
        }
    }
}

impl OxiaStandalone {
    pub fn with_image(mut self, image_name: String) -> Self {
        self.image_name = image_name;
        self
    }

    pub fn with_tag(mut self, tag: String) -> Self {
        self.tag = tag;
        self
    }

    pub fn with_log_level(mut self, log_level: String) -> Self {
        self.log_level = log_level;
        self
    }
}

impl Image for OxiaStandalone {
    fn name(&self) -> &str {
        self.image_name.as_str()
    }

    fn tag(&self) -> &str {
        self.tag.as_str()
    }

    fn ready_conditions(&self) -> Vec<WaitFor> {
        vec![WaitFor::message_on_stdout("Started Grpc server")]
    }

    fn cmd(&self) -> impl IntoIterator<Item = impl Into<Cow<'_, str>>> {
        vec!["bin/oxia", "standalone", "--log-level", &self.log_level]
    }
    fn expose_ports(&self) -> &[ContainerPort] {
        &[EXTERNAL_PORT, INTERNAL_PORT]
    }
}

#[cfg(test)]
mod test {
    use super::*;
    use liboxia::client::Client;
    use liboxia::client_builder::OxiaClientBuilder;
    use testcontainers::ImageExt;
    use testcontainers::core::logs::consumer;
    use testcontainers::runners::AsyncRunner;

    #[tokio::test]
    async fn test_standalone() {
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
        let get_result = client.get(key).await.unwrap();
        assert_eq!(put_result.key, get_result.key);
        assert_eq!(put_result.version.version_id, get_result.version.version_id);
    }
}
