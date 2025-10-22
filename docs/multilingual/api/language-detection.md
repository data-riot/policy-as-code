# Language Detection API

## 🔍 **Language Detection API Documentation**

This document outlines the Language Detection API for the Policy as Code platform, enabling automatic language detection for Nordic-Baltic languages.

## 🎯 **Overview**

The Language Detection API provides comprehensive language detection services for:

- **Text Language Detection**: Automatic text language detection
- **Document Language Detection**: Document language detection
- **Real-time Detection**: Real-time language detection
- **Batch Detection**: Batch language detection processing

## 🔧 **API Endpoints**

### **Text Language Detection**

#### **POST /api/v1/detect-language**
Detect the language of input text.

**Request Body:**
```json
{
  "text": "Hei, miten voit?",
  "context": "citizen_service",
  "confidence_threshold": 0.8
}
```

**Response:**
```json
{
  "detected_language": "fi",
  "confidence": 0.95,
  "alternative_languages": [
    {
      "language": "sv",
      "confidence": 0.15
    },
    {
      "language": "no",
      "confidence": 0.10
    }
  ],
  "text_length": 15,
  "detection_method": "statistical"
}
```

### **Document Language Detection**

#### **POST /api/v1/detect-language/document**
Detect the language of entire documents.

**Request Body:**
```json
{
  "document": "base64_encoded_document",
  "document_type": "pdf",
  "context": "legal_document",
  "confidence_threshold": 0.8
}
```

**Response:**
```json
{
  "detected_language": "sv",
  "confidence": 0.92,
  "alternative_languages": [
    {
      "language": "no",
      "confidence": 0.25
    },
    {
      "language": "da",
      "confidence": 0.18
    }
  ],
  "document_type": "pdf",
  "word_count": 1250,
  "detection_method": "hybrid"
}
```

### **Batch Language Detection**

#### **POST /api/v1/detect-language/batch**
Detect languages of multiple texts in batch.

**Request Body:**
```json
{
  "texts": [
    {
      "id": "text_1",
      "text": "Velkommen til vores service"
    },
    {
      "id": "text_2",
      "text": "Takk fyrir umsóknina þína"
    }
  ],
  "context": "citizen_service",
  "confidence_threshold": 0.8
}
```

**Response:**
```json
{
  "detections": [
    {
      "id": "text_1",
      "detected_language": "da",
      "confidence": 0.98
    },
    {
      "id": "text_2",
      "detected_language": "is",
      "confidence": 0.96
    }
  ],
  "overall_confidence": 0.97
}
```

## 🌍 **Supported Languages**

### **Nordic Languages**
- **Finnish (fi)**: Finnish language detection
- **Swedish (sv)**: Swedish language detection
- **Norwegian (no)**: Norwegian language detection (Bokmål)
- **Norwegian Nynorsk (nn)**: Norwegian Nynorsk detection
- **Danish (da)**: Danish language detection
- **Icelandic (is)**: Icelandic language detection

### **Baltic Languages**
- **Estonian (et)**: Estonian language detection
- **Latvian (lv)**: Latvian language detection
- **Lithuanian (lt)**: Lithuanian language detection

### **Other Languages**
- **English (en)**: English language detection
- **German (de)**: German language detection
- **French (fr)**: French language detection

## 🔍 **Detection Methods**

### **Statistical Detection**
- **N-gram Analysis**: Character and word n-gram analysis
- **Frequency Analysis**: Language-specific frequency patterns
- **Pattern Recognition**: Language-specific pattern recognition
- **Machine Learning**: Machine learning-based detection

### **Hybrid Detection**
- **Multiple Methods**: Combination of detection methods
- **Confidence Weighting**: Weighted confidence scoring
- **Context Awareness**: Context-aware detection
- **Fallback Mechanisms**: Fallback detection methods

### **Real-time Detection**
- **Streaming Detection**: Real-time streaming detection
- **Low Latency**: Low latency detection
- **Incremental Detection**: Incremental detection updates
- **Adaptive Thresholds**: Adaptive confidence thresholds

## 🎯 **Detection Contexts**

### **Government Service**
- **Formal Language**: Formal government language detection
- **Legal Terminology**: Legal terminology detection
- **Official Communication**: Official communication detection
- **Citizen Service**: Citizen service language detection

### **Legal Document**
- **Legal Terminology**: Legal terminology detection
- **Precision Requirements**: High precision detection
- **Legal Context**: Legal context detection
- **Compliance**: Legal compliance detection

### **Citizen Communication**
- **Informal Language**: Informal language detection
- **Regional Dialects**: Regional dialect detection
- **Cultural Context**: Cultural context detection
- **Accessibility**: Accessible language detection

## 🔧 **Detection Features**

### **Confidence Scoring**
- **Confidence Levels**: Multiple confidence levels
- **Threshold Management**: Configurable confidence thresholds
- **Alternative Languages**: Alternative language suggestions
- **Uncertainty Handling**: Uncertainty handling mechanisms

### **Performance**
- **Fast Detection**: Fast language detection
- **Batch Processing**: Efficient batch processing
- **Caching**: Detection result caching
- **Scalability**: Scalable detection services

### **Accuracy**
- **High Accuracy**: High detection accuracy
- **False Positive Reduction**: False positive reduction
- **Edge Case Handling**: Edge case handling
- **Continuous Improvement**: Continuous accuracy improvement

## 🚀 **Implementation Status**

### **Current Status**
- **✅ Basic Detection**: Basic language detection support
- **✅ Nordic Languages**: Nordic language detection support
- **✅ Confidence Scoring**: Confidence scoring support
- **⚠️ Advanced Features**: Advanced detection features in development

### **Planned Features**
- **Document Detection**: Enhanced document detection
- **Real-time Detection**: Real-time detection capabilities
- **Voice Detection**: Voice language detection
- **Cultural Adaptation**: Enhanced cultural adaptation

## 📖 **Usage Examples**

### **Python SDK**
```python
from policy_as_code.language_detection import LanguageDetectionClient

client = LanguageDetectionClient()

# Detect language
result = client.detect_language(
    text="Hei, miten voit?",
    context="citizen_service"
)

print(result.detected_language)  # "fi"
print(result.confidence)  # 0.95
```

### **REST API**
```bash
curl -X POST "http://localhost:8000/api/v1/detect-language" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Velkommen til vores service",
    "context": "citizen_service"
  }'
```

## 📚 **Resources**

- **Language Detection Models**: [Language Detection Models](https://huggingface.co/models?pipeline_tag=text-classification&search=language+detection)
- **Nordic Language Resources**: [Nordic Language Resources](https://www.nordiclanguage.org/)
- **Detection Accuracy**: [Detection Accuracy](https://www.detectionaccuracy.org/)
- **Language Patterns**: [Language Patterns](https://www.languagepatterns.org/)

## 🔗 **Related Documentation**

- **Multilingual Support**: [Multilingual Guide](../nordic-languages.md)
- **Translation API**: [Translation API](translation.md)
- **Cultural Context**: [Cultural Context API](cultural-context.md)
- **Cross-Language**: [Cross-Language API](cross-language.md)

---

**Status**: Basic Implementation Complete ✅ | Advanced Features in Development 🚧
