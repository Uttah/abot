.PHONY: build clean run

IMAGE_NAME := anonbot:local
CONTAINER_NAME := anonbot_local

build:
	docker build -t $(IMAGE_NAME) .

run: build
	docker run --rm -itd --name $(CONTAINER_NAME) \
		-v $(PWD)/:/app \
		$(IMAGE_NAME)

clean:
	docker rm -f $(CONTAINER_NAME) || true
	docker rmi $(IMAGE_NAME) || true
