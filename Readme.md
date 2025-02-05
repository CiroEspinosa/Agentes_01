  AlejandrIA Architecture 3.0

This project is designed to update and optimize the technological infrastructure of AlejandrIA by adopting a **3.0 architecture**. This architecture is based on a series of key principles and practices to improve scalability, flexibility, operational efficiency, and the ability to adapt to multiple environments and platforms.

The project involves transitioning to an event-driven microservices architecture, with the implementation of containers and Kubernetes, supporting multiple programming languages and databases, and using **LLMs (Large Language Models)** for general use and **SLMs (Specialized Language Models)** for specific cases.

## Features and Requirements

### 1. Migration to an Event-Driven Microservices Approach
- **Objective**: The 3.0 architecture focuses on the creation and operation of event-driven microservices, enabling agile and scalable responses to business changes. Each microservice is focused on a specific business function and communicates with others through events.
- **Benefits**: Provides better separation of concerns, greater flexibility and scalability, and quick responses to system events.
- **Technologies**: Technologies such as **Apache Kafka** for messaging and **RabbitMQ** for event management are implemented within this approach.

### 2. Container and Kubernetes-Based Deployment
- **Objective**: Container-based deployment with Kubernetes facilitates system integration and management at a multiplatform level. This enables easy portability and scaling of the project across different environments such as **EKS (Elastic Kubernetes Service)**, **AKS (Azure Kubernetes Service)**, **Kyma**, and **OpenShift**.
- **Benefits**: Containers encapsulate applications and services, making deployment and scaling easy across multiple platforms. Kubernetes automates orchestration, scaling, and availability of microservices.
- **Technologies**: **Docker** and **Kubernetes** are used for container deployment and management.

### 3. Multilingual Approach
- **Objective**: The 3.0 architecture adopts a multilingual approach, selecting the best programming language for each component or service based on its characteristics and requirements. This enables the optimization of system performance and efficiency.
- **Benefits**: Choosing the appropriate language improves software quality and enables better interoperability and flexibility.
- **Technologies**: **Python**, **Node.js**, **Java**, and other languages are used depending on specific needs.

### 4. Multi-Database Support
- **Objective**: Multi-database support is provided to manage the various needs and requirements of clients. This includes both relational and vector databases for storing and accessing different types of data.
- **Benefits**: Allows efficient management of heterogeneous data and provides greater flexibility in solution design and implementation.

### 5. LLMs for General Use and SLMs Fine-Tuned for Experts
- **Objective**: Large Language Models (LLMs) are used for general-purpose natural language processing and data analysis, alongside fine-tuned **Specialized Language Models (SLMs)** to address specific problems and needs of expert agents.
- **Benefits**: Leverages advanced machine learning to offer more personalized and tailored solutions for complex tasks.
- **Technologies**: OpenAI models like **GPT** and other LLMs fine-tuned based on project requirements.


# AlexandrIA's Agentic Framework

**AlexandrIA** introduces a streamlined and efficient workflow where specialized micro-services collaborate to achieve global objectives without wasting resources. By assigning distinct tasks to specialized agents rather than relying on a general-purpose agent, AlexandrIA optimizes individual agent performance. This approach results in superior overall outcomes compared to other AI solutions. Furthermore, AlexandrIA employs a unique memory management system that preserves relevant parts of the conversation while avoiding overload from outdated or unnecessary information. This allows conversations to remain coherent and focused, ensuring user queries are fully addressed.

## Agent Roles and the **RACI Matrix**

Each agent in AlexandrIA's ecosystem focuses solely on its designated task. This is made possible through the integration of OpenAI's **RACI** agent matrix (*Responsible, Accountable, Consulted, Informed*). Based on their assigned roles, agents adopt specialized approaches to their tasks and delegate responsibilities that fall outside their scope. This enables seamless communication between agents within the same *swarm*, effectively functioning as a self-organized, task-oriented enterprise.

The system's prompts establish a clear set of rules for agents, simplifying the coding process. This not only saves time but also facilitates the development of new tools and capabilities. Developers can extend AlexandrIA's functionality or tailor it to meet specific needs with ease, thanks to this modular approach.

### Example Workflow: The **RACI Matrix in Action**

Here’s a practical example of how AlexandrIA's workflow operates:

1. **The Initializer** (Responsible): The initializer agent receives the user's request. It acts as the **Responsible** party, initiating the workflow.
2. **The Admin** (Accountable): The initializer forwards the request to the admin agent, designated as the **Accountable** party. The admin oversees the process, ensuring the task is completed efficiently.
3. **Consulted Agents**: The admin queries the relevant **Consulted** agents for information based on predefined guidelines. These agents provide detailed data and insights necessary to achieve the goal with precision.
4. **Informed Agents**: Supporting agents may act as **Informed** participants, staying updated to assist if required.
5. **Execution and Completion**: Following the admin’s instructions, the consulted and informed agents work collaboratively to resolve the request. Once completed, the initializer compiles the final response and delivers it to the user.

Although this process involves intricate inter-agent communication, the division of tasks ensures near-instantaneous responses from the user’s perspective.

## Scalability and Reusability

One of AlexandrIA's standout features is the ability to define and deploy multiple *swarms* of agents. Agents can be reused across different swarms, enabling unparalleled scalability and efficiency. This modularity not only enhances productivity but also ensures that resources are allocated intelligently, maximizing the system’s potential across diverse applications.



# Data in AlexandrIA

DataX is the suite of GenAI use cases for data engineering & management implemented in AlejandrIA. It is a partner for development teams, leveraging Generative AI to support the entire data assets lifecycle. Targeted at Data Engineers, its goal is to drive greater efficiencies, enabling teams to concentrate on more complex problems and pursue more ambitious goals. DataX is implemented as a multi-agent system, focusing on improving productivity and the quality of Data Asset development through a hybrid approach (human/AI). These agents collaborate with engineers to complete tasks independently for subsequent review.

# Modifications

Due to the needs of the project, there have been a few modifications on the core to display a new attribute on the message characteristic ``pending_user_reply``. This attribute shows if the chain of messages between the agents ended or not. It's a boolean value set to ``None`` when the message is from the user, ``False`` when the agents are talking, and ``True`` on the last chain message, when the user can reply to the agents swarm properly.

This attribute is managed by detecting when the message is sent to the ``initializer`` at the end of the chain.

## Introduction

The first integration of **AlexandrIA** with **DataX** has focused on three main use cases:

1. **Case 0**: Creation of the semantic layer for each client/project.
2. **Case 1**: Generation of quality rules given a table.
3. **Case 2**: Generation of the necessary code to meet a functional requirement.
4. **Case 3**: To Be Defined.

Current version includes the implementasion of the **Case 1** detailed in the the [backend section](./back-v3/README.md).
The corresponding demo can be found on the [link](https://myoffice.accenture.com/:v:/r/personal/ruben_casado_tejedor_accenture_com/Documents/GenAI/AlejandrIA_DataX_demo.mp4?csf=1&web=1&nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJPbmVEcml2ZUZvckJ1c2luZXNzIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXciLCJyZWZlcnJhbFZpZXciOiJNeUZpbGVzTGlua0NvcHkifX0&e=OzmcjW).

To launch the **Case 1**:

1. Install as prerequisites *Docker* and *docker-compose*
2. For the backend, in the [back-v3](./back-v3) directory run the following command: `docker compose up --build`, check the [README](./back-v3/README.md). Assure the *.env* is completed
3. For the frontend, in the [frontend](./front) directory run the following command: `npm install`. Assure before that the *.env* is completed. Check the [README](./front/README.md). 
4. In the [frontend](./front) directory run the following command: `npm run dev` 


# Contacts
* Rubén Casado - ruben.casado.tejedor@accenture.com (DataX)
* Jose Chamorro - jose.chamorro@accenture.com (AlexandrIA)
* Jose Bernal - jose.bernal.blanco@accenture.com (AlexandrIA)
* Elisa Fernández - e.fernandez.maraver@accenture.com (DataX)
