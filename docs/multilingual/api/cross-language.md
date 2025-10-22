# Cross-Language API

## 🌐 **Cross-Language API Documentation**

This document outlines the Cross-Language API for the Policy as Code platform, enabling cross-language communication and services across Nordic-Baltic countries.

## 🎯 **Overview**

The Cross-Language API provides comprehensive cross-language services for:

- **Cross-Language Communication**: Communication across different languages
- **Cross-Language Services**: Services accessible in multiple languages
- **Cross-Language Data**: Data processing across languages
- **Cross-Language Integration**: Integration across language boundaries

## 🔧 **API Endpoints**

### **Cross-Language Communication**

#### **POST /api/v1/cross-language/communicate**
Enable communication across different languages.

**Request Body:**
```json
{
  "message": "Hei, miten voit?",
  "source_language": "fi",
  "target_languages": ["sv", "no", "da"],
  "context": "citizen_service",
  "communication_purpose": "information_sharing"
}
```

**Response:**
```json
{
  "translations": [
    {
      "language": "sv",
      "translated_message": "Hej, hur mår du?",
      "confidence": 0.95
    },
    {
      "language": "no",
      "translated_message": "Hei, hvordan har du det?",
      "confidence": 0.92
    },
    {
      "language": "da",
      "translated_message": "Hej, hvordan har du det?",
      "confidence": 0.90
    }
  ],
  "cultural_adaptations": [
    {
      "language": "sv",
      "adaptation": "lagom_formality",
      "reason": "Swedish preference for balanced formality"
    }
  ]
}
```

### **Cross-Language Service Access**

#### **POST /api/v1/cross-language/service**
Access services in multiple languages.

**Request Body:**
```json
{
  "service_id": "citizen_benefits",
  "user_language": "is",
  "available_languages": ["fi", "sv", "no", "da", "is"],
  "service_context": "benefit_application"
}
```

**Response:**
```json
{
  "service_access": {
    "service_id": "citizen_benefits",
    "available_in_language": true,
    "language": "is",
    "service_interface": {
      "language": "is",
      "interface_elements": [
        {
          "element": "welcome_message",
          "text": "Velkomin í ríkisþjónustuna"
        },
        {
          "element": "application_form",
          "text": "Umsóknarform"
        }
      ]
    }
  },
  "fallback_options": [
    {
      "language": "en",
      "reason": "English fallback available"
    }
  ]
}
```

### **Cross-Language Data Processing**

#### **POST /api/v1/cross-language/process-data**
Process data across different languages.

**Request Body:**
```json
{
  "data": [
    {
      "id": "data_1",
      "text": "Velkommen til vores service",
      "language": "da"
    },
    {
      "id": "data_2",
      "text": "Tervetuloa palveluumme",
      "language": "fi"
    }
  ],
  "processing_type": "sentiment_analysis",
  "target_language": "en",
  "context": "citizen_feedback"
}
```

**Response:**
```json
{
  "processed_data": [
    {
      "id": "data_1",
      "original_text": "Velkommen til vores service",
      "original_language": "da",
      "processed_result": {
        "sentiment": "positive",
        "confidence": 0.92,
        "translated_text": "Welcome to our service"
      }
    },
    {
      "id": "data_2",
      "original_text": "Tervetuloa palveluumme",
      "original_language": "fi",
      "processed_result": {
        "sentiment": "positive",
        "confidence": 0.95,
        "translated_text": "Welcome to our service"
      }
    }
  ],
  "cross_language_insights": {
    "common_sentiment": "positive",
    "language_distribution": {
      "da": 1,
      "fi": 1
    }
  }
}
```

## 🌍 **Supported Cross-Language Features**

### **Language Pairs**
- **Nordic Languages**: All Nordic language combinations
- **Baltic Languages**: All Baltic language combinations
- **Cross-Regional**: Nordic-Baltic language combinations
- **International**: English and other major languages

### **Communication Types**
- **Synchronous**: Real-time cross-language communication
- **Asynchronous**: Delayed cross-language communication
- **Batch**: Batch cross-language processing
- **Streaming**: Streaming cross-language communication

### **Service Types**
- **Government Services**: Cross-language government services
- **Citizen Services**: Cross-language citizen services
- **Legal Services**: Cross-language legal services
- **Administrative Services**: Cross-language administrative services

## 🔧 **Cross-Language Features**

### **Translation**
- **Real-time Translation**: Real-time cross-language translation
- **Batch Translation**: Batch cross-language translation
- **Context-Aware Translation**: Context-aware translation
- **Cultural Adaptation**: Cultural adaptation in translation

### **Communication**
- **Multi-Language Support**: Multi-language communication support
- **Language Detection**: Automatic language detection
- **Fallback Mechanisms**: Language fallback mechanisms
- **Quality Assurance**: Translation quality assurance

### **Integration**
- **API Integration**: Cross-language API integration
- **Service Integration**: Cross-language service integration
- **Data Integration**: Cross-language data integration
- **Workflow Integration**: Cross-language workflow integration

## 🚀 **Implementation Status**

### **Current Status**
- **✅ Basic Cross-Language**: Basic cross-language support
- **✅ Nordic Languages**: Nordic cross-language support
- **✅ Translation**: Cross-language translation
- **⚠️ Advanced Features**: Advanced cross-language features in development

### **Planned Features**
- **Real-time Communication**: Real-time cross-language communication
- **Advanced Integration**: Advanced cross-language integration
- **Cultural Adaptation**: Enhanced cultural adaptation
- **Quality Assurance**: Enhanced quality assurance

## 📖 **Usage Examples**

### **Python SDK**
```python
from policy_as_code.cross_language import CrossLanguageClient

client = CrossLanguageClient()

# Cross-language communication
result = client.communicate(
    message="Hei, miten voit?",
    source_language="fi",
    target_languages=["sv", "no", "da"],
    context="citizen_service"
)

for translation in result.translations:
    print(f"{translation.language}: {translation.translated_message}")
```

### **REST API**
```bash
curl -X POST "http://localhost:8000/api/v1/cross-language/communicate" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Velkommen til vores service",
    "source_language": "da",
    "target_languages": ["fi", "sv", "no"],
    "context": "citizen_service"
  }'
```

## 📚 **Resources**

- **Cross-Language Models**: [Cross-Language Models](https://huggingface.co/models?pipeline_tag=translation&search=cross+language)
- **Nordic Language Resources**: [Nordic Language Resources](https://www.nordiclanguage.org/)
- **Cross-Language Research**: [Cross-Language Research](https://www.crosslanguageresearch.org/)
- **Multilingual Communication**: [Multilingual Communication](https://www.multilingualcommunication.org/)

## 🔗 **Related Documentation**

- **Multilingual Support**: [Multilingual Guide](../nordic-languages.md)
- **Translation API**: [Translation API](translation.md)
- **Language Detection**: [Language Detection API](language-detection.md)
- **Cultural Context**: [Cultural Context API](cultural-context.md)

---

**Status**: Basic Implementation Complete ✅ | Advanced Features in Development 🚧
