# Translation API

## 🌐 **Translation API Documentation**

This document outlines the Translation API for the Policy as Code platform, enabling multilingual translation services across Nordic-Baltic countries.

## 🎯 **Overview**

The Translation API provides comprehensive translation services for:

- **Text Translation**: Text translation between Nordic-Baltic languages
- **Document Translation**: Document translation services
- **Real-time Translation**: Real-time translation capabilities
- **Batch Translation**: Batch translation processing

## 🔧 **API Endpoints**

### **Text Translation**

#### **POST /api/v1/translate**
Translate text between supported languages.

**Request Body:**
```json
{
  "text": "Hello, how are you?",
  "source_language": "en",
  "target_language": "fi",
  "context": "government_service",
  "formality": "formal"
}
```

**Response:**
```json
{
  "translated_text": "Hei, miten voit?",
  "confidence": 0.95,
  "source_language": "en",
  "target_language": "fi",
  "context": "government_service",
  "formality": "formal"
}
```

### **Document Translation**

#### **POST /api/v1/translate/document**
Translate entire documents.

**Request Body:**
```json
{
  "document": "base64_encoded_document",
  "document_type": "pdf",
  "source_language": "sv",
  "target_language": "no",
  "context": "legal_document"
}
```

**Response:**
```json
{
  "translated_document": "base64_encoded_translated_document",
  "confidence": 0.92,
  "source_language": "sv",
  "target_language": "no",
  "context": "legal_document",
  "word_count": 1250
}
```

### **Batch Translation**

#### **POST /api/v1/translate/batch**
Translate multiple texts in batch.

**Request Body:**
```json
{
  "texts": [
    {
      "id": "text_1",
      "text": "Welcome to our service",
      "source_language": "en",
      "target_language": "da"
    },
    {
      "id": "text_2",
      "text": "Thank you for your application",
      "source_language": "en",
      "target_language": "is"
    }
  ],
  "context": "citizen_service"
}
```

**Response:**
```json
{
  "translations": [
    {
      "id": "text_1",
      "translated_text": "Velkommen til vores service",
      "confidence": 0.98
    },
    {
      "id": "text_2",
      "translated_text": "Takk fyrir umsóknina þína",
      "confidence": 0.96
    }
  ],
  "overall_confidence": 0.97
}
```

## 🌍 **Supported Languages**

### **Nordic Languages**
- **Finnish (fi)**: Finnish language support
- **Swedish (sv)**: Swedish language support
- **Norwegian (no)**: Norwegian language support (Bokmål)
- **Norwegian Nynorsk (nn)**: Norwegian Nynorsk support
- **Danish (da)**: Danish language support
- **Icelandic (is)**: Icelandic language support

### **Baltic Languages**
- **Estonian (et)**: Estonian language support
- **Latvian (lv)**: Latvian language support
- **Lithuanian (lt)**: Lithuanian language support

### **Other Languages**
- **English (en)**: English language support
- **German (de)**: German language support
- **French (fr)**: French language support

## 🎯 **Translation Contexts**

### **Government Service**
- **Formal Language**: Formal government language
- **Legal Terminology**: Legal terminology support
- **Official Communication**: Official communication style
- **Citizen Service**: Citizen service language

### **Legal Document**
- **Legal Terminology**: Legal terminology support
- **Precision Requirements**: High precision requirements
- **Legal Context**: Legal context preservation
- **Compliance**: Legal compliance requirements

### **Citizen Communication**
- **Friendly Tone**: Friendly and approachable tone
- **Clear Language**: Clear and understandable language
- **Cultural Sensitivity**: Cultural sensitivity
- **Accessibility**: Accessible language

## 🔧 **Translation Features**

### **Context Awareness**
- **Domain-Specific Translation**: Domain-specific terminology
- **Cultural Context**: Cultural context preservation
- **Formality Levels**: Appropriate formality levels
- **Regional Variations**: Regional language variations

### **Quality Assurance**
- **Confidence Scoring**: Translation confidence scoring
- **Quality Metrics**: Translation quality metrics
- **Human Review**: Human review for critical translations
- **Feedback Integration**: User feedback integration

### **Performance**
- **Caching**: Translation result caching
- **Batch Processing**: Efficient batch processing
- **Real-time Translation**: Real-time translation capabilities
- **Scalability**: Scalable translation services

## 🚀 **Implementation Status**

### **Current Status**
- **✅ Basic Translation**: Basic text translation support
- **✅ Language Support**: Nordic-Baltic language support
- **✅ Context Awareness**: Basic context awareness
- **⚠️ Advanced Features**: Advanced translation features in development

### **Planned Features**
- **Document Translation**: Enhanced document translation
- **Real-time Translation**: Real-time translation capabilities
- **Voice Translation**: Voice translation support
- **Cultural Adaptation**: Enhanced cultural adaptation

## 📖 **Usage Examples**

### **Python SDK**
```python
from policy_as_code.translation import TranslationClient

client = TranslationClient()

# Translate text
result = client.translate(
    text="Welcome to our government service",
    source_language="en",
    target_language="fi",
    context="citizen_service"
)

print(result.translated_text)  # "Tervetuloa hallituksen palveluun"
```

### **REST API**
```bash
curl -X POST "http://localhost:8000/api/v1/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your application has been approved",
    "source_language": "en",
    "target_language": "sv",
    "context": "citizen_service"
  }'
```

## 📚 **Resources**

- **Translation Models**: [Translation Models](https://huggingface.co/models?pipeline_tag=translation)
- **Nordic Language Resources**: [Nordic Language Resources](https://www.nordiclanguage.org/)
- **Translation Quality**: [Translation Quality](https://www.translationquality.org/)
- **Cultural Context**: [Cultural Context](https://www.culturalcontext.org/)

## 🔗 **Related Documentation**

- **Multilingual Support**: [Multilingual Guide](../nordic-languages.md)
- **Language Detection**: [Language Detection API](language-detection.md)
- **Cultural Context**: [Cultural Context API](cultural-context.md)
- **Cross-Language**: [Cross-Language API](cross-language.md)

---

**Status**: Basic Implementation Complete ✅ | Advanced Features in Development 🚧
